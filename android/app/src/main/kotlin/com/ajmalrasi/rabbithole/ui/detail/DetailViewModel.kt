package com.ajmalrasi.rabbithole.ui.detail

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ajmalrasi.rabbithole.data.repository.RabbitHoleRepository
import com.ajmalrasi.rabbithole.domain.model.RabbitHoleDetail
import com.ajmalrasi.rabbithole.ui.common.UiState
import com.ajmalrasi.rabbithole.util.ChatGptLauncher
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class AskUiState(
    val question: String = "",
    val launchError: String? = null,
)

@HiltViewModel
class DetailViewModel @Inject constructor(
    private val repository: RabbitHoleRepository,
    savedStateHandle: SavedStateHandle,
) : ViewModel() {

    private val id: Int = checkNotNull(savedStateHandle.get<String>("id")).toInt()

    private val _state = MutableStateFlow<UiState<RabbitHoleDetail>>(UiState.Loading)
    val state: StateFlow<UiState<RabbitHoleDetail>> = _state.asStateFlow()

    private val _askState = MutableStateFlow(AskUiState())
    val askState: StateFlow<AskUiState> = _askState.asStateFlow()

    val isFavorite: StateFlow<Boolean> = repository.observeIsFavorite(id)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), false)

    init {
        load()
    }

    fun load() {
        viewModelScope.launch {
            _state.value = UiState.Loading
            val result = repository.getRabbitHole(id)
            _state.value = result.fold(
                onSuccess = { detail ->
                    _askState.update {
                        it.copy(
                            question = ChatGptLauncher.buildDefaultPrompt(detail),
                            launchError = null,
                        )
                    }
                    UiState.Success(detail)
                },
                onFailure = { UiState.Error("Couldn't load this rabbit hole.") },
            )
        }
    }

    fun toggleFavorite() {
        viewModelScope.launch {
            repository.toggleFavorite(id, isFavorite.value)
        }
    }

    fun onQuestionChange(text: String) {
        _askState.update { it.copy(question = text, launchError = null) }
    }

    fun reportLaunchError(message: String) {
        _askState.update { it.copy(launchError = message) }
    }
}
