package com.ajmalrasi.rabbithole

import android.app.Application
import com.ajmalrasi.rabbithole.data.remote.DynamicBaseUrlInterceptor
import com.ajmalrasi.rabbithole.data.settings.SettingsRepository
import dagger.hilt.android.HiltAndroidApp
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltAndroidApp
class RabbitHoleApp : Application() {

    @Inject
    lateinit var settingsRepository: SettingsRepository

    @Inject
    lateinit var baseUrlInterceptor: DynamicBaseUrlInterceptor

    private val appScope = CoroutineScope(SupervisorJob())

    override fun onCreate() {
        super.onCreate()
        appScope.launch {
            settingsRepository.apiBaseUrl
                .onEach { baseUrlInterceptor.setBaseUrl(it) }
                .collect {}
        }
    }
}
