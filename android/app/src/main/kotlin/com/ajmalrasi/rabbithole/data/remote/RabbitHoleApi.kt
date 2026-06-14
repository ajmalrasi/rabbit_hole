package com.ajmalrasi.rabbithole.data.remote

import com.ajmalrasi.rabbithole.data.remote.dto.AskRequestDto
import com.ajmalrasi.rabbithole.data.remote.dto.AskResponseDto
import com.ajmalrasi.rabbithole.data.remote.dto.AdminStatusDto
import com.ajmalrasi.rabbithole.data.remote.dto.CategoriesResponseDto
import com.ajmalrasi.rabbithole.data.remote.dto.FeedResponseDto
import com.ajmalrasi.rabbithole.data.remote.dto.PipelineActionDto
import com.ajmalrasi.rabbithole.data.remote.dto.RabbitHoleDetailDto
import com.ajmalrasi.rabbithole.data.remote.dto.SearchResponseDto
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface RabbitHoleApi {
    @GET("feed")
    suspend fun getFeed(
        @Query("limit") limit: Int = 20,
        @Query("offset") offset: Int = 0,
        @Query("category") category: String? = null,
    ): FeedResponseDto

    @GET("rabbit-hole/{id}")
    suspend fun getRabbitHole(@Path("id") id: Int): RabbitHoleDetailDto

    @POST("rabbit-hole/{id}/ask")
    suspend fun askQuestion(
        @Path("id") id: Int,
        @Body body: AskRequestDto,
    ): AskResponseDto

    @GET("categories")
    suspend fun getCategories(): CategoriesResponseDto

    @GET("search")
    suspend fun search(
        @Query("q") query: String,
        @Query("limit") limit: Int = 20,
        @Query("semantic") semantic: Boolean = true,
    ): SearchResponseDto

    @GET("admin/status")
    suspend fun getAdminStatus(): AdminStatusDto

    @POST("admin/pipeline/run")
    suspend fun runPipeline(
        @Query("ingest") ingest: Boolean = true,
        @Query("drain") drain: Boolean = true,
    ): PipelineActionDto

    @POST("admin/pipeline/fetch")
    suspend fun fetchFeeds(): PipelineActionDto

    @POST("admin/pipeline/process")
    suspend fun processArticles(@Query("drain") drain: Boolean = true): PipelineActionDto

    @POST("admin/feed/rebuild")
    suspend fun rebuildFeed(): PipelineActionDto
}
