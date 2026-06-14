package com.ajmalrasi.rabbithole.ui.search

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ajmalrasi.rabbithole.data.repository.RabbitHoleRepository
import com.ajmalrasi.rabbithole.domain.model.SearchResult
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class SearchUiState(
    val query: String = "",
    val semantic: Boolean = true,
    val results: List<SearchResult> = emptyList(),
    val isLoading: Boolean = false,
    val hasSearched: Boolean = false,
    val errorMessage: String? = null,
)

@HiltViewModel
class SearchViewModel @Inject constructor(
    private val repository: RabbitHoleRepository,
) : ViewModel() {

    private val _state = MutableStateFlow(SearchUiState())
    val state: StateFlow<SearchUiState> = _state.asStateFlow()

    fun onQueryChange(query: String) {
        _state.value = _state.value.copy(query = query)
    }

    fun toggleSemantic() {
        _state.value = _state.value.copy(semantic = !_state.value.semantic)
    }

    fun search() {
        val query = _state.value.query.trim()
        if (query.isEmpty()) return
        viewModelScope.launch {
            _state.value = _state.value.copy(isLoading = true, errorMessage = null, hasSearched = true)
            val result = repository.search(query, _state.value.semantic)
            _state.value = result.fold(
                onSuccess = { _state.value.copy(results = it, isLoading = false) },
                onFailure = {
                    _state.value.copy(
                        isLoading = false,
                        errorMessage = "Search failed. Check your connection.",
                    )
                },
            )
        }
    }
}
