package com.ajmalrasi.rabbithole.ui.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ajmalrasi.rabbithole.data.settings.SettingsRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val settingsRepository: SettingsRepository,
) : ViewModel() {

    val apiBaseUrl: StateFlow<String> = settingsRepository.apiBaseUrl
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), "")

    fun saveApiBaseUrl(url: String) {
        viewModelScope.launch {
            settingsRepository.setApiBaseUrl(url)
        }
    }
}
