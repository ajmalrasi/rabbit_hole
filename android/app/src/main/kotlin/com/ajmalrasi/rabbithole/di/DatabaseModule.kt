package com.ajmalrasi.rabbithole.di

import android.content.Context
import androidx.room.Room
import com.ajmalrasi.rabbithole.data.local.RabbitHoleDatabase
import com.ajmalrasi.rabbithole.data.local.dao.CategoryDao
import com.ajmalrasi.rabbithole.data.local.dao.DetailDao
import com.ajmalrasi.rabbithole.data.local.dao.FavoriteDao
import com.ajmalrasi.rabbithole.data.local.dao.FeedDao
import com.ajmalrasi.rabbithole.data.local.dao.SearchDao
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): RabbitHoleDatabase =
        Room.databaseBuilder(context, RabbitHoleDatabase::class.java, "rabbit_hole.db")
            .fallbackToDestructiveMigration(dropAllTables = true)
            .build()

    @Provides
    fun provideFeedDao(db: RabbitHoleDatabase): FeedDao = db.feedDao()

    @Provides
    fun provideDetailDao(db: RabbitHoleDatabase): DetailDao = db.detailDao()

    @Provides
    fun provideCategoryDao(db: RabbitHoleDatabase): CategoryDao = db.categoryDao()

    @Provides
    fun provideFavoriteDao(db: RabbitHoleDatabase): FavoriteDao = db.favoriteDao()

    @Provides
    fun provideSearchDao(db: RabbitHoleDatabase): SearchDao = db.searchDao()
}
