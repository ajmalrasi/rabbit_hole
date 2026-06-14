package com.ajmalrasi.rabbithole.ui.favorites

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ajmalrasi.rabbithole.data.repository.RabbitHoleRepository
import com.ajmalrasi.rabbithole.domain.model.RabbitHoleSummary
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import javax.inject.Inject

@HiltViewModel
class FavoritesViewModel @Inject constructor(
    repository: RabbitHoleRepository,
) : ViewModel() {

    val favorites: StateFlow<List<RabbitHoleSummary>> = repository.observeFavorites()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())
}
