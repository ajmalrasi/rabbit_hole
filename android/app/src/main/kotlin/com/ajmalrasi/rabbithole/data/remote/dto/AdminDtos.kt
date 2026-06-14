package com.ajmalrasi.rabbithole.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class PipelineCountersDto(
    val ingested: Int = 0,
    val scored: Int = 0,
    val passed: Int = 0,
    val rejected: Int = 0,
    val generated: Int = 0,
    val duplicates: Int = 0,
    val failed: Int = 0,
    @SerialName("feed_size") val feedSize: Int = 0,
)

@Serializable
data class PipelineRunStateDto(
    val running: Boolean,
    val stage: String,
    @SerialName("stage_total") val stageTotal: Int,
    @SerialName("stage_processed") val stageProcessed: Int,
    @SerialName("stage_elapsed_seconds") val stageElapsedSeconds: Double,
    @SerialName("stage_eta_seconds") val stageEtaSeconds: Double? = null,
    @SerialName("started_at") val startedAt: String? = null,
    @SerialName("finished_at") val finishedAt: String? = null,
    @SerialName("run_elapsed_seconds") val runElapsedSeconds: Double? = null,
    val drain: Boolean,
    val counters: PipelineCountersDto,
    val errors: List<String> = emptyList(),
)

@Serializable
data class ArticleStatusCountsDto(
    val new: Int = 0,
    val scored: Int = 0,
    val rejected: Int = 0,
    val generated: Int = 0,
    val duplicate: Int = 0,
    val failed: Int = 0,
)

@Serializable
data class AdminStatusDto(
    val app: String,
    val version: String,
    @SerialName("llm_provider") val llmProvider: String,
    @SerialName("embedding_provider") val embeddingProvider: String,
    val database: String,
    @SerialName("daily_feed_size") val dailyFeedSize: Int,
    @SerialName("total_rabbit_holes") val totalRabbitHoles: Int,
    @SerialName("feed_count") val feedCount: Int,
    val articles: ArticleStatusCountsDto,
    val pipeline: PipelineRunStateDto,
)

@Serializable
data class PipelineActionDto(
    val status: String,
    val stage: String? = null,
)
