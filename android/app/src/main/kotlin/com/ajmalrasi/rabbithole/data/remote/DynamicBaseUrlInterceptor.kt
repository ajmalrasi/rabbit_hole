package com.ajmalrasi.rabbithole.data.remote

import okhttp3.HttpUrl.Companion.toHttpUrlOrNull
import okhttp3.Interceptor
import okhttp3.Response
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Rewrites the scheme/host/port of every request to match the user-configured
 * API base URL, so the base URL can change at runtime without rebuilding Retrofit.
 */
@Singleton
class DynamicBaseUrlInterceptor @Inject constructor() : Interceptor {

    @Volatile
    private var baseUrl: String = "http://192.168.3.30:8000"

    fun setBaseUrl(url: String) {
        baseUrl = url
    }

    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        val target = baseUrl.toHttpUrlOrNull() ?: return chain.proceed(request)
        val newUrl = request.url.newBuilder()
            .scheme(target.scheme)
            .host(target.host)
            .port(target.port)
            .build()
        return chain.proceed(request.newBuilder().url(newUrl).build())
    }
}
