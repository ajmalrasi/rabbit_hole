package com.ajmalrasi.rabbithole.ui.feed

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.derivedStateOf
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.ajmalrasi.rabbithole.ui.common.EmptyState
import com.ajmalrasi.rabbithole.ui.common.LoadingState
import com.ajmalrasi.rabbithole.ui.common.RabbitHoleCard
import com.ajmalrasi.rabbithole.ui.common.RabbitHoleListDivider

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FeedScreen(
    onItemClick: (Int) -> Unit,
    modifier: Modifier = Modifier,
    viewModel: FeedViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val listState = rememberLazyListState()

    val shouldLoadMore by remember {
        derivedStateOf {
            val lastVisible = listState.layoutInfo.visibleItemsInfo.lastOrNull()?.index ?: -1
            val headerRows = 1 + if (state.categories.isNotEmpty()) 1 else 0
            val bottomIndex = headerRows + state.items.size // footer row
            lastVisible >= bottomIndex - 1 &&
                state.hasMore &&
                !state.isLoadingMore &&
                !state.isRefreshing &&
                state.items.isNotEmpty()
        }
    }

    LaunchedEffect(shouldLoadMore) {
        if (shouldLoadMore) viewModel.loadMore()
    }

    PullToRefreshBox(
        isRefreshing = state.isRefreshing,
        onRefresh = viewModel::refresh,
        modifier = modifier.fillMaxSize(),
    ) {
        when {
            state.items.isEmpty() && state.isRefreshing -> LoadingState()
            state.items.isEmpty() && state.errorMessage != null ->
                EmptyState(
                    title = "No feed yet",
                    subtitle = state.errorMessage ?: "Pull down to refresh.",
                )
            state.items.isEmpty() ->
                EmptyState(
                    title = if (state.selectedCategory != null) "No items in this topic" else "Nothing here yet",
                    subtitle = "Pull to refresh or try another category.",
                )
            else -> LazyColumn(
                state = listState,
                modifier = Modifier.fillMaxSize(),
                contentPadding = PaddingValues(vertical = 12.dp),
            ) {
                item {
                    FeedHeader(
                        selectedCategory = state.selectedCategory,
                        shown = state.items.size,
                        total = state.total,
                    )
                }
                if (state.categories.isNotEmpty()) {
                    item {
                        CategoryFilterRow(
                            categories = state.categories,
                            selected = state.selectedCategory,
                            onSelect = viewModel::selectCategory,
                        )
                        Spacer(Modifier.height(8.dp))
                    }
                }
                items(state.items, key = { it.id }) { item ->
                    RabbitHoleCard(item = item, onClick = { onItemClick(item.id) })
                    RabbitHoleListDivider()
                }
                if (state.hasMore) {
                    item {
                        LoadMoreFooter(isLoading = state.isLoadingMore)
                    }
                } else if (state.items.isNotEmpty()) {
                    item {
                        Text(
                            text = "End of feed",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(24.dp),
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun FeedHeader(selectedCategory: String?, shown: Int, total: Int) {
    Column(Modifier.padding(horizontal = 20.dp, vertical = 8.dp)) {
        Text(
            text = if (selectedCategory != null) selectedCategory else "Today's rabbit holes",
            style = MaterialTheme.typography.displaySmall,
            color = MaterialTheme.colorScheme.onBackground,
        )
        Spacer(Modifier.height(4.dp))
        Text(
            text = if (total > 0) {
                "Showing $shown of $total · The invisible systems behind ordinary things"
            } else {
                "The invisible systems behind ordinary things"
            },
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
    Spacer(Modifier.height(8.dp))
}

@Composable
private fun LoadMoreFooter(isLoading: Boolean) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 20.dp, vertical = 20.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        if (isLoading) {
            LinearProgressIndicator(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(4.dp)
                    .clip(RoundedCornerShape(50)),
            )
            Spacer(Modifier.height(10.dp))
            Text(
                text = "Loading 10 more…",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        } else {
            Text(
                text = "Scroll for more",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun CategoryFilterRow(
    categories: List<com.ajmalrasi.rabbithole.domain.model.CategoryCount>,
    selected: String?,
    onSelect: (String?) -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .horizontalScroll(rememberScrollState())
            .padding(horizontal = 20.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        FilterChip(
            selected = selected == null,
            onClick = { onSelect(null) },
            label = { Text("All") },
        )
        categories
            .sortedWith(
                compareBy<com.ajmalrasi.rabbithole.domain.model.CategoryCount> { cat ->
                    when (cat.category.lowercase()) {
                        "engineering" -> 0
                        "infrastructure", "manufacturing", "architecture", "transportation" -> 1
                        "physics", "chemistry" -> 2
                        else -> 3
                    }
                }.thenByDescending { it.count },
            )
            .forEach { cat ->
            FilterChip(
                selected = selected?.equals(cat.category, ignoreCase = true) == true,
                onClick = { onSelect(cat.category) },
                label = { Text("${cat.category} (${cat.count})") },
            )
        }
    }
}
