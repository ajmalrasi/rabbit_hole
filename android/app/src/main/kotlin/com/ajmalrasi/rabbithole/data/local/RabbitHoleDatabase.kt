package com.ajmalrasi.rabbithole.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import com.ajmalrasi.rabbithole.data.local.dao.CategoryDao
import com.ajmalrasi.rabbithole.data.local.dao.DetailDao
import com.ajmalrasi.rabbithole.data.local.dao.FavoriteDao
import com.ajmalrasi.rabbithole.data.local.dao.FeedDao
import com.ajmalrasi.rabbithole.data.local.dao.SearchDao
import com.ajmalrasi.rabbithole.data.local.entity.CachedDetailEntity
import com.ajmalrasi.rabbithole.data.local.entity.CachedSummaryEntity
import com.ajmalrasi.rabbithole.data.local.entity.CategoryEntity
import com.ajmalrasi.rabbithole.data.local.entity.FavoriteEntity
import com.ajmalrasi.rabbithole.data.local.entity.FeedMetaEntity
import com.ajmalrasi.rabbithole.data.local.entity.SearchCacheEntity

@Database(
    entities = [
        CachedSummaryEntity::class,
        CachedDetailEntity::class,
        CategoryEntity::class,
        FavoriteEntity::class,
        SearchCacheEntity::class,
        FeedMetaEntity::class,
    ],
    version = 1,
    exportSchema = false,
)
abstract class RabbitHoleDatabase : RoomDatabase() {
    abstract fun feedDao(): FeedDao
    abstract fun detailDao(): DetailDao
    abstract fun categoryDao(): CategoryDao
    abstract fun favoriteDao(): FavoriteDao
    abstract fun searchDao(): SearchDao
}
