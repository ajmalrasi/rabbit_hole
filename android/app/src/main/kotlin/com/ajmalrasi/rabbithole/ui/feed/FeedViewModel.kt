package com.ajmalrasi.rabbithole.ui.feed

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ajmalrasi.rabbithole.data.repository.RabbitHoleRepository
import com.ajmalrasi.rabbithole.data.settings.SettingsRepository
import com.ajmalrasi.rabbithole.domain.model.CategoryCount
import com.ajmalrasi.rabbithole.domain.model.RabbitHoleSummary
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class FeedUiState(
    val items: List<RabbitHoleSummary> = emptyList(),
    val categories: List<CategoryCount> = emptyList(),
    val selectedCategory: String? = null,
    val total: Int = 0,
    val isRefreshing: Boolean = false,
    val isLoadingMore: Boolean = false,
    val hasMore: Boolean = false,
    val errorMessage: String? = null,
)

@HiltViewModel
class FeedViewModel @Inject constructor(
    private val repository: RabbitHoleRepository,
    private val settingsRepository: SettingsRepository,
) : ViewModel() {

    private val _state = MutableStateFlow(FeedUiState(isRefreshing = true))
    val uiState: StateFlow<FeedUiState> = _state.asStateFlow()

    /** Prevents duplicate load-more calls while the footer stays on screen. */
    private var lastLoadOffset: Int = -1

    init {
        loadCategories()
        viewModelScope.launch {
            val category = settingsRepository.preferredFeedCategoryOnce()
            _state.update { it.copy(selectedCategory = category?.ifBlank { null }) }
            refresh()
        }
    }

    private fun loadCategories() {
        viewModelScope.launch {
            repository.refreshCategories()
            repository.observeCategories().collect { categories ->
                _state.update { it.copy(categories = categories) }
            }
        }
    }

    fun refresh() {
        viewModelScope.launch {
            lastLoadOffset = -1
            _state.update { it.copy(isRefreshing = true, errorMessage = null) }
            val category = _state.value.selectedCategory
            val result = repository.refreshFeed(category = category)
            _state.update { current ->
                result.fold(
                    onSuccess = { page ->
                        current.copy(
                            items = page.items,
                            total = page.total,
                            hasMore = page.items.size < page.total,
                            isRefreshing = false,
                        )
                    },
                    onFailure = {
                        current.copy(
                            isRefreshing = false,
                            errorMessage = "Couldn't reach the server. Pull to retry.",
                        )
                    },
                )
            }
        }
    }

    fun loadMore() {
        val current = _state.value
        val offset = current.items.size
        if (current.isLoadingMore || current.isRefreshing || !current.hasMore) return
        if (lastLoadOffset == offset) return
        lastLoadOffset = offset
        viewModelScope.launch {
            _state.update { it.copy(isLoadingMore = true) }
            val result = repository.loadMoreFeed(
                offset = offset,
                category = current.selectedCategory,
            )
            _state.update { state ->
                result.fold(
                    onSuccess = { page ->
                        val merged = state.items + page.items
                        state.copy(
                            items = merged,
                            total = page.total,
                            hasMore = merged.size < page.total,
                            isLoadingMore = false,
                        )
                    },
                    onFailure = {
                        lastLoadOffset = -1
                        state.copy(isLoadingMore = false)
                    },
                )
            }
        }
    }

    fun selectCategory(category: String?) {
        if (_state.value.selectedCategory == category) return
        lastLoadOffset = -1
        _state.update { it.copy(selectedCategory = category, items = emptyList()) }
        viewModelScope.launch {
            settingsRepository.setPreferredFeedCategory(category)
            refresh()
        }
    }
}
