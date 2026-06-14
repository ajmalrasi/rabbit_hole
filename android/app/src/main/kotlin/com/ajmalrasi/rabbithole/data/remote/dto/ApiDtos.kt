package com.ajmalrasi.rabbithole.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class RabbitHoleSummaryDto(
    val id: Int,
    val title: String,
    val observation: String,
    val question: String,
    val category: String,
    @SerialName("curiosity_score") val curiosityScore: Double,
    @SerialName("hidden_mechanism_score") val hiddenMechanismScore: Double,
    @SerialName("source_url") val sourceUrl: String,
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class RabbitHoleDetailDto(
    val id: Int,
    val title: String,
    val observation: String,
    val question: String,
    @SerialName("hidden_mechanism") val hiddenMechanism: String,
    val explanation: String,
    @SerialName("interesting_fact") val interestingFact: String,
    @SerialName("why_it_matters") val whyItMatters: String,
    @SerialName("follow_up_question") val followUpQuestion: String,
    val category: String,
    @SerialName("source_url") val sourceUrl: String,
    @SerialName("curiosity_score") val curiosityScore: Double,
    @SerialName("hidden_mechanism_score") val hiddenMechanismScore: Double,
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class FeedResponseDto(
    val count: Int,
    val total: Int,
    @SerialName("generated_at") val generatedAt: String,
    val items: List<RabbitHoleSummaryDto>,
)

@Serializable
data class AskRequestDto(
    val question: String,
)

@Serializable
data class AskResponseDto(
    val answer: String,
    val provider: String,
)

@Serializable
data class CategoryCountDto(
    val category: String,
    val count: Int,
)

@Serializable
data class CategoriesResponseDto(
    val categories: List<CategoryCountDto>,
)

@Serializable
data class SearchResultDto(
    val id: Int,
    val title: String,
    val observation: String,
    val question: String,
    val category: String,
    @SerialName("curiosity_score") val curiosityScore: Double,
    @SerialName("hidden_mechanism_score") val hiddenMechanismScore: Double,
    @SerialName("source_url") val sourceUrl: String,
    @SerialName("created_at") val createdAt: String,
    val distance: Double? = null,
)

@Serializable
data class SearchResponseDto(
    val query: String,
    val count: Int,
    val results: List<SearchResultDto>,
)
