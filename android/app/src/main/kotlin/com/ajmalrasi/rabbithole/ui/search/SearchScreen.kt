package com.ajmalrasi.rabbithole.ui.search

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Search
import androidx.compose.material3.Icon
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.ajmalrasi.rabbithole.ui.common.EmptyState
import com.ajmalrasi.rabbithole.ui.common.LoadingState
import com.ajmalrasi.rabbithole.ui.common.RabbitHoleCard
import com.ajmalrasi.rabbithole.ui.common.RabbitHoleListDivider

@Composable
fun SearchScreen(
    onItemClick: (Int) -> Unit,
    modifier: Modifier = Modifier,
    viewModel: SearchViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    Column(modifier = modifier.fillMaxSize().padding(horizontal = 20.dp)) {
        Spacer(Modifier.height(16.dp))
        Text(
            text = "Search",
            style = MaterialTheme.typography.displaySmall,
            color = MaterialTheme.colorScheme.onBackground,
        )
        Spacer(Modifier.height(12.dp))
        OutlinedTextField(
            value = state.query,
            onValueChange = viewModel::onQueryChange,
            modifier = Modifier.fillMaxWidth(),
            placeholder = { Text("Ask anything…") },
            leadingIcon = { Icon(Icons.Outlined.Search, contentDescription = null) },
            singleLine = true,
            keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search),
            keyboardActions = KeyboardActions(onSearch = { viewModel.search() }),
        )
        Spacer(Modifier.height(10.dp))
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            FilterChip(
                selected = state.semantic,
                onClick = viewModel::toggleSemantic,
                label = { Text(if (state.semantic) "Meaning" else "Keyword") },
            )
            Text(
                text = if (state.semantic) "Searches by concept" else "Matches exact words",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        Spacer(Modifier.height(8.dp))

        when {
            state.isLoading -> LoadingState()
            state.errorMessage != null && state.results.isEmpty() ->
                EmptyState(title = "No results", subtitle = state.errorMessage!!)
            state.hasSearched && state.results.isEmpty() ->
                EmptyState(title = "No results", subtitle = "Try different words or toggle the search mode.")
            !state.hasSearched ->
                EmptyState(title = "What are you curious about?", subtitle = "Search across every rabbit hole.")
            else -> LazyColumn(Modifier.fillMaxSize()) {
                items(state.results, key = { it.summary.id }) { result ->
                    RabbitHoleCard(item = result.summary, onClick = { onItemClick(result.summary.id) })
                    RabbitHoleListDivider()
                }
            }
        }
    }
}
