package com.ajmalrasi.rabbithole.data.repository

import com.ajmalrasi.rabbithole.data.local.dao.CategoryDao
import com.ajmalrasi.rabbithole.data.local.dao.DetailDao
import com.ajmalrasi.rabbithole.data.local.dao.FavoriteDao
import com.ajmalrasi.rabbithole.data.local.dao.FeedDao
import com.ajmalrasi.rabbithole.data.local.dao.SearchDao
import com.ajmalrasi.rabbithole.data.local.entity.CategoryEntity
import com.ajmalrasi.rabbithole.data.local.entity.FavoriteEntity
import com.ajmalrasi.rabbithole.data.local.entity.FeedMetaEntity
import com.ajmalrasi.rabbithole.data.local.entity.SearchCacheEntity
import com.ajmalrasi.rabbithole.data.mapper.toDomain
import com.ajmalrasi.rabbithole.data.mapper.toEntity
import com.ajmalrasi.rabbithole.data.remote.dto.AskRequestDto
import com.ajmalrasi.rabbithole.data.remote.RabbitHoleApi
import com.ajmalrasi.rabbithole.domain.model.AdminStatus
import com.ajmalrasi.rabbithole.domain.model.CategoryCount
import com.ajmalrasi.rabbithole.domain.model.RabbitHoleDetail
import com.ajmalrasi.rabbithole.domain.model.RabbitHoleSummary
import com.ajmalrasi.rabbithole.domain.model.SearchResult
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class RabbitHoleRepository @Inject constructor(
    private val api: RabbitHoleApi,
    private val feedDao: FeedDao,
    private val detailDao: DetailDao,
    private val categoryDao: CategoryDao,
    private val favoriteDao: FavoriteDao,
    private val searchDao: SearchDao,
) {
    companion object {
        const val FEED_PAGE_SIZE = 10
    }

    data class FeedPage(
        val items: List<RabbitHoleSummary>,
        val total: Int,
    )

    fun observeFeed(): Flow<List<RabbitHoleSummary>> =
        feedDao.observeFeed().map { items -> items.map { it.toDomain() } }

    fun observeFeedMeta(): Flow<FeedMetaEntity?> = feedDao.observeFeedMeta()

    suspend fun refreshFeed(
        category: String? = null,
        limit: Int = FEED_PAGE_SIZE,
    ): Result<FeedPage> = fetchFeedPage(offset = 0, category = category, limit = limit, replace = true)

    suspend fun loadMoreFeed(
        offset: Int,
        category: String? = null,
        limit: Int = FEED_PAGE_SIZE,
    ): Result<FeedPage> = fetchFeedPage(offset = offset, category = category, limit = limit, replace = false)

    private suspend fun fetchFeedPage(
        offset: Int,
        category: String?,
        limit: Int,
        replace: Boolean,
    ): Result<FeedPage> = runCatching {
        val response = api.getFeed(limit = limit, offset = offset, category = category)
        val items = response.items.map { it.toDomain() }
        if (replace) {
            feedDao.clearFeed()
        }
        val startRank = if (replace) 1 else (feedDao.getFeed().size + 1)
        feedDao.insertSummaries(
            items.mapIndexed { index, summary ->
                summary.toEntity(feedRank = startRank + index)
            },
        )
        if (replace) {
            feedDao.insertFeedMeta(
                FeedMetaEntity(
                    generatedAt = response.generatedAt,
                    cachedAt = System.currentTimeMillis(),
                ),
            )
        }
        FeedPage(items = items, total = response.total)
    }.recoverCatching {
        val cached = feedDao.getFeed().map { it.toDomain() }
        val filtered = if (category == null) {
            cached
        } else {
            cached.filter { it.category.equals(category, ignoreCase = true) }
        }
        FeedPage(items = filtered, total = filtered.size)
    }

    suspend fun askQuestion(id: Int, question: String): Result<Pair<String, String>> = runCatching {
        val response = api.askQuestion(id, AskRequestDto(question.trim()))
        response.answer to response.provider
    }

    suspend fun getRabbitHole(id: Int): Result<RabbitHoleDetail> = runCatching {
        val remote = api.getRabbitHole(id).toDomain()
        detailDao.insertDetail(remote.toEntity())
        val summary = remote.let { detail ->
            RabbitHoleSummary(
                id = detail.id,
                title = detail.title,
                observation = detail.observation,
                question = detail.question,
                category = detail.category,
                curiosityScore = detail.curiosityScore,
                hiddenMechanismScore = detail.hiddenMechanismScore,
                sourceUrl = detail.sourceUrl,
                createdAt = detail.createdAt,
            )
        }
        feedDao.insertSummaries(listOf(summary.toEntity()))
        remote
    }.recoverCatching {
        detailDao.getDetail(id)?.toDomain()
            ?: throw it
    }

    fun observeCategories(): Flow<List<CategoryCount>> =
        categoryDao.observeCategories().map { items -> items.map { it.toDomain() } }

    suspend fun refreshCategories(): Result<List<CategoryCount>> = runCatching {
        val response = api.getCategories()
        categoryDao.clear()
        val entities = response.categories.map { CategoryEntity(it.category, it.count) }
        categoryDao.insertAll(entities)
        entities.map { it.toDomain() }
    }.recoverCatching {
        categoryDao.getCategories().map { it.toDomain() }
    }

    suspend fun getCategoryItems(category: String): Result<List<RabbitHoleSummary>> = runCatching {
        val response = api.search(query = category, semantic = false, limit = 50)
        val items = response.results.map { it.toDomain().summary }
        val now = System.currentTimeMillis()
        searchDao.clearQuery("category:$category")
        searchDao.insertResults(
            items.map { summary ->
                SearchCacheEntity(
                    query = "category:$category",
                    resultId = summary.id,
                    title = summary.title,
                    observation = summary.observation,
                    question = summary.question,
                    category = summary.category,
                    curiosityScore = summary.curiosityScore,
                    hiddenMechanismScore = summary.hiddenMechanismScore,
                    sourceUrl = summary.sourceUrl,
                    createdAt = summary.createdAt,
                    cachedAt = now,
                )
            },
        )
        feedDao.insertSummaries(items.map { it.toEntity() })
        items
    }.recoverCatching {
        searchDao.getResults("category:$category").map { cached ->
            RabbitHoleSummary(
                id = cached.resultId,
                title = cached.title,
                observation = cached.observation,
                question = cached.question,
                category = cached.category,
                curiosityScore = cached.curiosityScore,
                hiddenMechanismScore = cached.hiddenMechanismScore,
                sourceUrl = cached.sourceUrl,
                createdAt = cached.createdAt,
            )
        }.ifEmpty {
            searchDao.getByCategory(category).map { it.toDomain() }
        }
    }

    suspend fun search(query: String, semantic: Boolean = true): Result<List<SearchResult>> =
        runCatching {
            val response = api.search(query = query, semantic = semantic)
            val results = response.results.map { it.toDomain() }
            val now = System.currentTimeMillis()
            searchDao.clearQuery(query)
            searchDao.insertResults(
                results.map { result ->
                    SearchCacheEntity(
                        query = query,
                        resultId = result.summary.id,
                        title = result.summary.title,
                        observation = result.summary.observation,
                        question = result.summary.question,
                        category = result.summary.category,
                        curiosityScore = result.summary.curiosityScore,
                        hiddenMechanismScore = result.summary.hiddenMechanismScore,
                        sourceUrl = result.summary.sourceUrl,
                        createdAt = result.summary.createdAt,
                        cachedAt = now,
                    )
                },
            )
            feedDao.insertSummaries(results.map { it.summary.toEntity() })
            results
        }.recoverCatching {
            searchDao.getResults(query).map { cached ->
                SearchResult(
                    summary = RabbitHoleSummary(
                        id = cached.resultId,
                        title = cached.title,
                        observation = cached.observation,
                        question = cached.question,
                        category = cached.category,
                        curiosityScore = cached.curiosityScore,
                        hiddenMechanismScore = cached.hiddenMechanismScore,
                        sourceUrl = cached.sourceUrl,
                        createdAt = cached.createdAt,
                    ),
                )
            }
        }

    fun observeFavorites(): Flow<List<RabbitHoleSummary>> =
        favoriteDao.observeFavorites().map { items -> items.map { it.toDomain() } }

    fun observeIsFavorite(id: Int): Flow<Boolean> = favoriteDao.observeIsFavorite(id)

    suspend fun toggleFavorite(id: Int, isFavorite: Boolean) {
        if (isFavorite) {
            favoriteDao.removeFavorite(id)
        } else {
            favoriteDao.addFavorite(FavoriteEntity(rabbitHoleId = id, savedAt = System.currentTimeMillis()))
        }
    }

    // ----- admin / pipeline -----

    suspend fun getAdminStatus(): Result<AdminStatus> = runCatching {
        api.getAdminStatus().toDomain()
    }

    suspend fun runPipeline(): Result<String> = runCatching {
        api.runPipeline().status
    }

    suspend fun fetchFeeds(): Result<String> = runCatching {
        api.fetchFeeds().status
    }

    suspend fun processArticles(): Result<String> = runCatching {
        api.processArticles().status
    }

    suspend fun rebuildFeed(): Result<String> = runCatching {
        api.rebuildFeed().status
    }
}
