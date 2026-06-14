package com.ajmalrasi.rabbithole.ui.admin

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ajmalrasi.rabbithole.data.repository.RabbitHoleRepository
import com.ajmalrasi.rabbithole.domain.model.AdminStatus
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import javax.inject.Inject

data class AdminUiState(
    val status: AdminStatus? = null,
    val loading: Boolean = true,
    val errorMessage: String? = null,
    val actionInFlight: Boolean = false,
    val actionMessage: String? = null,
)

@HiltViewModel
class AdminViewModel @Inject constructor(
    private val repository: RabbitHoleRepository,
) : ViewModel() {

    private val _state = MutableStateFlow(AdminUiState())
    val state: StateFlow<AdminUiState> = _state.asStateFlow()

    init {
        startPolling()
    }

    private fun startPolling() {
        viewModelScope.launch {
            while (isActive) {
                refresh()
                // Poll faster while a run is active, slower when idle.
                val running = _state.value.status?.pipeline?.running == true
                delay(if (running) 2_000 else 6_000)
            }
        }
    }

    private suspend fun refresh() {
        val result = repository.getAdminStatus()
        _state.update { current ->
            result.fold(
                onSuccess = {
                    current.copy(status = it, loading = false, errorMessage = null)
                },
                onFailure = {
                    current.copy(
                        loading = false,
                        errorMessage = "Can't reach the server.",
                    )
                },
            )
        }
    }

    fun runFullPipeline() = trigger("Full pipeline started") { repository.runPipeline() }

    fun fetchFeeds() = trigger("Fetching RSS feeds") { repository.fetchFeeds() }

    fun processArticles() = trigger("Processing queue") { repository.processArticles() }

    fun rebuildFeed() = trigger("Rebuilding feed") { repository.rebuildFeed() }

    private fun trigger(successMessage: String, action: suspend () -> Result<String>) {
        viewModelScope.launch {
            _state.update { it.copy(actionInFlight = true, actionMessage = null) }
            val result = action()
            _state.update {
                it.copy(
                    actionInFlight = false,
                    actionMessage = result.fold(
                        onSuccess = { status ->
                            if (status == "already_running") {
                                "A run is already in progress"
                            } else {
                                successMessage
                            }
                        },
                        onFailure = { "Action failed — check connection" },
                    ),
                )
            }
            refresh()
        }
    }

    fun clearActionMessage() {
        _state.update { it.copy(actionMessage = null) }
    }
}
