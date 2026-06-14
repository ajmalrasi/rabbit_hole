package com.ajmalrasi.rabbithole.ui.categories

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ajmalrasi.rabbithole.data.repository.RabbitHoleRepository
import com.ajmalrasi.rabbithole.domain.model.CategoryCount
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

data class CategoriesUiState(
    val categories: List<CategoryCount> = emptyList(),
    val isLoading: Boolean = true,
    val errorMessage: String? = null,
)

@HiltViewModel
class CategoriesViewModel @Inject constructor(
    private val repository: RabbitHoleRepository,
) : ViewModel() {

    private val loading = MutableStateFlow(true)
    private val error = MutableStateFlow<String?>(null)

    val uiState: StateFlow<CategoriesUiState> = combine(
        repository.observeCategories(),
        loading,
        error,
    ) { categories, isLoading, errorMessage ->
        CategoriesUiState(categories = categories, isLoading = isLoading, errorMessage = errorMessage)
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = CategoriesUiState(),
    )

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            loading.value = true
            error.value = null
            val result = repository.refreshCategories()
            if (result.isFailure) {
                error.value = "Couldn't load topics."
            }
            loading.value = false
        }
    }
}
