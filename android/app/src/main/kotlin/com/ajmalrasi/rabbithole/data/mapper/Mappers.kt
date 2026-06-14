package com.ajmalrasi.rabbithole.data.mapper

import com.ajmalrasi.rabbithole.data.local.entity.CachedDetailEntity
import com.ajmalrasi.rabbithole.data.local.entity.CachedSummaryEntity
import com.ajmalrasi.rabbithole.data.local.entity.CategoryEntity
import com.ajmalrasi.rabbithole.data.remote.dto.AdminStatusDto
import com.ajmalrasi.rabbithole.data.remote.dto.CategoryCountDto
import com.ajmalrasi.rabbithole.data.remote.dto.RabbitHoleDetailDto
import com.ajmalrasi.rabbithole.data.remote.dto.RabbitHoleSummaryDto
import com.ajmalrasi.rabbithole.data.remote.dto.SearchResultDto
import com.ajmalrasi.rabbithole.domain.model.AdminStatus
import com.ajmalrasi.rabbithole.domain.model.ArticleStatusCounts
import com.ajmalrasi.rabbithole.domain.model.CategoryCount
import com.ajmalrasi.rabbithole.domain.model.PipelineRunState
import com.ajmalrasi.rabbithole.domain.model.RabbitHoleDetail
import com.ajmalrasi.rabbithole.domain.model.RabbitHoleSummary
import com.ajmalrasi.rabbithole.domain.model.SearchResult

fun RabbitHoleSummaryDto.toDomain(): RabbitHoleSummary = RabbitHoleSummary(
    id = id,
    title = title,
    observation = observation,
    question = question,
    category = category,
    curiosityScore = curiosityScore,
    hiddenMechanismScore = hiddenMechanismScore,
    sourceUrl = sourceUrl,
    createdAt = createdAt,
)

fun RabbitHoleDetailDto.toDomain(): RabbitHoleDetail = RabbitHoleDetail(
    id = id,
    title = title,
    observation = observation,
    question = question,
    hiddenMechanism = hiddenMechanism,
    explanation = explanation,
    interestingFact = interestingFact,
    whyItMatters = whyItMatters,
    followUpQuestion = followUpQuestion,
    category = category,
    sourceUrl = sourceUrl,
    curiosityScore = curiosityScore,
    hiddenMechanismScore = hiddenMechanismScore,
    createdAt = createdAt,
)

fun SearchResultDto.toDomain(): SearchResult = SearchResult(
    summary = RabbitHoleSummary(
        id = id,
        title = title,
        observation = observation,
        question = question,
        category = category,
        curiosityScore = curiosityScore,
        hiddenMechanismScore = hiddenMechanismScore,
        sourceUrl = sourceUrl,
        createdAt = createdAt,
    ),
    distance = distance,
)

fun CategoryCountDto.toDomain(): CategoryCount = CategoryCount(
    category = category,
    count = count,
)

fun RabbitHoleSummary.toEntity(feedRank: Int? = null): CachedSummaryEntity = CachedSummaryEntity(
    id = id,
    title = title,
    observation = observation,
    question = question,
    category = category,
    curiosityScore = curiosityScore,
    hiddenMechanismScore = hiddenMechanismScore,
    sourceUrl = sourceUrl,
    createdAt = createdAt,
    feedRank = feedRank,
)

fun RabbitHoleDetail.toEntity(): CachedDetailEntity = CachedDetailEntity(
    id = id,
    title = title,
    observation = observation,
    question = question,
    hiddenMechanism = hiddenMechanism,
    explanation = explanation,
    interestingFact = interestingFact,
    whyItMatters = whyItMatters,
    followUpQuestion = followUpQuestion,
    category = category,
    sourceUrl = sourceUrl,
    curiosityScore = curiosityScore,
    hiddenMechanismScore = hiddenMechanismScore,
    createdAt = createdAt,
    cachedAt = System.currentTimeMillis(),
)

fun CachedSummaryEntity.toDomain(): RabbitHoleSummary = RabbitHoleSummary(
    id = id,
    title = title,
    observation = observation,
    question = question,
    category = category,
    curiosityScore = curiosityScore,
    hiddenMechanismScore = hiddenMechanismScore,
    sourceUrl = sourceUrl,
    createdAt = createdAt,
)

fun CachedDetailEntity.toDomain(): RabbitHoleDetail = RabbitHoleDetail(
    id = id,
    title = title,
    observation = observation,
    question = question,
    hiddenMechanism = hiddenMechanism,
    explanation = explanation,
    interestingFact = interestingFact,
    whyItMatters = whyItMatters,
    followUpQuestion = followUpQuestion,
    category = category,
    sourceUrl = sourceUrl,
    curiosityScore = curiosityScore,
    hiddenMechanismScore = hiddenMechanismScore,
    createdAt = createdAt,
)

fun CategoryEntity.toDomain(): CategoryCount = CategoryCount(
    category = category,
    count = count,
)

fun AdminStatusDto.toDomain(): AdminStatus = AdminStatus(
    app = app,
    version = version,
    llmProvider = llmProvider,
    embeddingProvider = embeddingProvider,
    database = database,
    dailyFeedSize = dailyFeedSize,
    totalRabbitHoles = totalRabbitHoles,
    feedCount = feedCount,
    articles = ArticleStatusCounts(
        new = articles.new,
        scored = articles.scored,
        rejected = articles.rejected,
        generated = articles.generated,
        duplicate = articles.duplicate,
        failed = articles.failed,
    ),
    pipeline = PipelineRunState(
        running = pipeline.running,
        stage = pipeline.stage,
        stageTotal = pipeline.stageTotal,
        stageProcessed = pipeline.stageProcessed,
        stageElapsedSeconds = pipeline.stageElapsedSeconds,
        stageEtaSeconds = pipeline.stageEtaSeconds,
        runElapsedSeconds = pipeline.runElapsedSeconds,
        drain = pipeline.drain,
        generated = pipeline.counters.generated,
        passed = pipeline.counters.passed,
        rejected = pipeline.counters.rejected,
        duplicates = pipeline.counters.duplicates,
        failed = pipeline.counters.failed,
        feedSize = pipeline.counters.feedSize,
        errors = pipeline.errors,
    ),
)
