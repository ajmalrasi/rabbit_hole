package com.ajmalrasi.rabbithole.ui.common

sealed interface UiState<out T> {
    data object Loading : UiState<Nothing>
    data class Success<T>(val data: T, val stale: Boolean = false) : UiState<T>
    data class Error(val message: String) : UiState<Nothing>
}
