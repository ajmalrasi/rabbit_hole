package com.ajmalrasi.rabbithole.ui.categories

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.ajmalrasi.rabbithole.ui.common.EmptyState
import com.ajmalrasi.rabbithole.ui.common.ErrorState
import com.ajmalrasi.rabbithole.ui.common.LoadingState
import com.ajmalrasi.rabbithole.ui.common.RabbitHoleCard
import com.ajmalrasi.rabbithole.ui.common.RabbitHoleListDivider
import com.ajmalrasi.rabbithole.ui.common.UiState

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CategoryItemsScreen(
    onBack: () -> Unit,
    onItemClick: (Int) -> Unit,
    viewModel: CategoryItemsViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(viewModel.category, style = MaterialTheme.typography.titleLarge) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.background,
                ),
            )
        },
    ) { padding ->
        when (val s = state) {
            is UiState.Loading -> LoadingState(Modifier.padding(padding))
            is UiState.Error -> ErrorState(s.message, onRetry = viewModel::load, modifier = Modifier.padding(padding))
            is UiState.Success -> if (s.data.isEmpty()) {
                EmptyState(
                    title = "Nothing here yet",
                    subtitle = "No rabbit holes in this topic.",
                    modifier = Modifier.padding(padding),
                )
            } else {
                LazyColumn(Modifier.fillMaxSize().padding(padding)) {
                    items(s.data, key = { it.id }) { item ->
                        RabbitHoleCard(item = item, onClick = { onItemClick(item.id) })
                        RabbitHoleListDivider()
                    }
                }
            }
        }
    }
}
