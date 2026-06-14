package com.ajmalrasi.rabbithole.ui.categories

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ajmalrasi.rabbithole.data.repository.RabbitHoleRepository
import com.ajmalrasi.rabbithole.domain.model.RabbitHoleSummary
import com.ajmalrasi.rabbithole.ui.common.UiState
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.net.URLDecoder
import javax.inject.Inject

@HiltViewModel
class CategoryItemsViewModel @Inject constructor(
    private val repository: RabbitHoleRepository,
    savedStateHandle: SavedStateHandle,
) : ViewModel() {

    val category: String = URLDecoder.decode(
        checkNotNull(savedStateHandle.get<String>("name")),
        "UTF-8",
    )

    private val _state = MutableStateFlow<UiState<List<RabbitHoleSummary>>>(UiState.Loading)
    val state: StateFlow<UiState<List<RabbitHoleSummary>>> = _state.asStateFlow()

    init {
        load()
    }

    fun load() {
        viewModelScope.launch {
            _state.value = UiState.Loading
            val result = repository.getCategoryItems(category)
            _state.value = result.fold(
                onSuccess = { UiState.Success(it) },
                onFailure = { UiState.Error("Couldn't load this topic.") },
            )
        }
    }
}
