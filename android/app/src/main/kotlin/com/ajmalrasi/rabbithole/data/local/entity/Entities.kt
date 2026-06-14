package com.ajmalrasi.rabbithole.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "cached_summaries")
data class CachedSummaryEntity(
    @PrimaryKey val id: Int,
    val title: String,
    val observation: String,
    val question: String,
    val category: String,
    val curiosityScore: Double,
    val hiddenMechanismScore: Double,
    val sourceUrl: String,
    val createdAt: String,
    val feedRank: Int? = null,
)

@Entity(tableName = "cached_details")
data class CachedDetailEntity(
    @PrimaryKey val id: Int,
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
    val cachedAt: Long,
)

@Entity(tableName = "categories")
data class CategoryEntity(
    @PrimaryKey val category: String,
    val count: Int,
)

@Entity(tableName = "favorites")
data class FavoriteEntity(
    @PrimaryKey val rabbitHoleId: Int,
    val savedAt: Long,
)

@Entity(tableName = "search_cache")
data class SearchCacheEntity(
    @PrimaryKey(autoGenerate = true) val cacheId: Long = 0,
    val query: String,
    val resultId: Int,
    val title: String,
    val observation: String,
    val question: String,
    val category: String,
    val curiosityScore: Double,
    val hiddenMechanismScore: Double,
    val sourceUrl: String,
    val createdAt: String,
    val cachedAt: Long,
)

@Entity(tableName = "feed_meta")
data class FeedMetaEntity(
    @PrimaryKey val id: Int = 1,
    val generatedAt: String,
    val cachedAt: Long,
)
