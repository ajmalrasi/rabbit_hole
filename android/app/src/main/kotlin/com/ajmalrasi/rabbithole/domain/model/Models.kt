package com.ajmalrasi.rabbithole.domain.model

data class RabbitHoleSummary(
    val id: Int,
    val title: String,
    val observation: String,
    val question: String,
    val category: String,
    val curiosityScore: Double,
    val hiddenMechanismScore: Double,
    val sourceUrl: String,
    val createdAt: String,
)

data class RabbitHoleDetail(
    val id: Int,
    val title: String,
    val observation: String,
    val question: String,
    val hiddenMechanism: String,
    val explanation: String,
    val interestingFact: String,
    val whyItMatters: String,
    val followUpQuestion: String,
    val category: String,
    val sourceUrl: String,
    val curiosityScore: Double,
    val hiddenMechanismScore: Double,
    val createdAt: String,
)

data class CategoryCount(
    val category: String,
    val count: Int,
)

data class SearchResult(
    val summary: RabbitHoleSummary,
    val distance: Double? = null,
)

data class AdminStatus(
    val app: String,
    val version: String,
    val llmProvider: String,
    val embeddingProvider: String,
    val database: String,
    val dailyFeedSize: Int,
    val totalRabbitHoles: Int,
    val feedCount: Int,
    val articles: ArticleStatusCounts,
    val pipeline: PipelineRunState,
)

data class ArticleStatusCounts(
    val new: Int,
    val scored: Int,
    val rejected: Int,
    val generated: Int,
    val duplicate: Int,
    val failed: Int,
)

data class PipelineRunState(
    val running: Boolean,
    val stage: String,
    val stageTotal: Int,
    val stageProcessed: Int,
    val stageElapsedSeconds: Double,
    val stageEtaSeconds: Double?,
    val runElapsedSeconds: Double?,
    val drain: Boolean,
    val generated: Int,
    val passed: Int,
    val rejected: Int,
    val duplicates: Int,
    val failed: Int,
    val feedSize: Int,
    val errors: List<String>,
)
