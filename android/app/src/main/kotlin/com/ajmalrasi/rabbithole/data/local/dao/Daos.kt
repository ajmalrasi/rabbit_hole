package com.ajmalrasi.rabbithole.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.ajmalrasi.rabbithole.data.local.entity.CachedDetailEntity
import com.ajmalrasi.rabbithole.data.local.entity.CachedSummaryEntity
import com.ajmalrasi.rabbithole.data.local.entity.CategoryEntity
import com.ajmalrasi.rabbithole.data.local.entity.FavoriteEntity
import com.ajmalrasi.rabbithole.data.local.entity.FeedMetaEntity
import com.ajmalrasi.rabbithole.data.local.entity.SearchCacheEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface FeedDao {
    @Query("SELECT * FROM cached_summaries WHERE feedRank IS NOT NULL ORDER BY feedRank ASC")
    fun observeFeed(): Flow<List<CachedSummaryEntity>>

    @Query("SELECT * FROM cached_summaries WHERE feedRank IS NOT NULL ORDER BY feedRank ASC")
    suspend fun getFeed(): List<CachedSummaryEntity>

    @Query("DELETE FROM cached_summaries WHERE feedRank IS NOT NULL")
    suspend fun clearFeed()

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertSummaries(items: List<CachedSummaryEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertFeedMeta(meta: FeedMetaEntity)

    @Query("SELECT * FROM feed_meta WHERE id = 1")
    fun observeFeedMeta(): Flow<FeedMetaEntity?>

    @Query("SELECT * FROM feed_meta WHERE id = 1")
    suspend fun getFeedMeta(): FeedMetaEntity?
}

@Dao
interface DetailDao {
    @Query("SELECT * FROM cached_details WHERE id = :id")
    suspend fun getDetail(id: Int): CachedDetailEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertDetail(detail: CachedDetailEntity)
}

@Dao
interface CategoryDao {
    @Query("SELECT * FROM categories ORDER BY count DESC")
    fun observeCategories(): Flow<List<CategoryEntity>>

    @Query("SELECT * FROM categories ORDER BY count DESC")
    suspend fun getCategories(): List<CategoryEntity>

    @Query("DELETE FROM categories")
    suspend fun clear()

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(items: List<CategoryEntity>)
}

@Dao
interface FavoriteDao {
    @Query(
        """
        SELECT s.* FROM cached_summaries s
        INNER JOIN favorites f ON s.id = f.rabbitHoleId
        ORDER BY f.savedAt DESC
        """,
    )
    fun observeFavorites(): Flow<List<CachedSummaryEntity>>

    @Query("SELECT EXISTS(SELECT 1 FROM favorites WHERE rabbitHoleId = :id)")
    fun observeIsFavorite(id: Int): Flow<Boolean>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun addFavorite(favorite: FavoriteEntity)

    @Query("DELETE FROM favorites WHERE rabbitHoleId = :id")
    suspend fun removeFavorite(id: Int)
}

@Dao
interface SearchDao {
    @Query("DELETE FROM search_cache WHERE query = :query")
    suspend fun clearQuery(query: String)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertResults(items: List<SearchCacheEntity>)

    @Query("SELECT * FROM search_cache WHERE query = :query ORDER BY cacheId ASC")
    suspend fun getResults(query: String): List<SearchCacheEntity>

    @Query(
        """
        SELECT * FROM cached_summaries
        WHERE LOWER(category) = LOWER(:category)
        ORDER BY curiosityScore DESC
        """,
    )
    suspend fun getByCategory(category: String): List<CachedSummaryEntity>
}
