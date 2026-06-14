package com.ajmalrasi.rabbithole.ui.favorites

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.ajmalrasi.rabbithole.ui.common.EmptyState
import com.ajmalrasi.rabbithole.ui.common.RabbitHoleCard
import com.ajmalrasi.rabbithole.ui.common.RabbitHoleListDivider

@Composable
fun FavoritesScreen(
    onItemClick: (Int) -> Unit,
    modifier: Modifier = Modifier,
    viewModel: FavoritesViewModel = hiltViewModel(),
) {
    val favorites by viewModel.favorites.collectAsStateWithLifecycle()

    if (favorites.isEmpty()) {
        EmptyState(
            title = "Nothing saved yet",
            subtitle = "Tap the bookmark on any rabbit hole to keep it here.",
            modifier = modifier,
        )
        return
    }

    LazyColumn(modifier = modifier.fillMaxSize()) {
        item {
            Column(Modifier.padding(horizontal = 20.dp, vertical = 16.dp)) {
                Text(
                    text = "Saved",
                    style = MaterialTheme.typography.displaySmall,
                    color = MaterialTheme.colorScheme.onBackground,
                )
                Spacer(Modifier.height(4.dp))
            }
        }
        items(favorites, key = { it.id }) { item ->
            RabbitHoleCard(item = item, onClick = { onItemClick(item.id) })
            RabbitHoleListDivider()
        }
    }
}
