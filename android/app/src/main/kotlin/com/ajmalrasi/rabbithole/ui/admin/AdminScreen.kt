package com.ajmalrasi.rabbithole.ui.admin

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.ajmalrasi.rabbithole.domain.model.AdminStatus
import com.ajmalrasi.rabbithole.domain.model.PipelineRunState
import com.ajmalrasi.rabbithole.ui.common.ErrorState
import com.ajmalrasi.rabbithole.ui.common.LoadingState

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AdminScreen(
    onBack: () -> Unit,
    viewModel: AdminViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    val snackbarHostState = remember { SnackbarHostState() }

    LaunchedEffect(state.actionMessage) {
        state.actionMessage?.let {
            snackbarHostState.showSnackbar(it)
            viewModel.clearActionMessage()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Pipeline admin", style = MaterialTheme.typography.titleLarge) },
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
        snackbarHost = { SnackbarHost(snackbarHostState) },
    ) { padding ->
        val status = state.status
        when {
            status == null && state.loading -> LoadingState(Modifier.padding(padding))
            status == null -> ErrorState(
                state.errorMessage ?: "No data",
                modifier = Modifier.padding(padding),
            )
            else -> LazyColumn(
                modifier = Modifier.padding(padding),
                contentPadding = PaddingValues(20.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
            ) {
                item { PipelineCard(status.pipeline) }
                item { FunnelCard(status) }
                item { ContentCard(status) }
                item { ServerCard(status) }
                if (status.pipeline.errors.isNotEmpty()) {
                    item { ErrorsCard(status.pipeline.errors) }
                }
                item {
                    ActionButtons(
                        inFlight = state.actionInFlight,
                        onRun = viewModel::runFullPipeline,
                        onFetch = viewModel::fetchFeeds,
                        onProcess = viewModel::processArticles,
                        onRebuild = viewModel::rebuildFeed,
                    )
                }
            }
        }
    }
}

@Composable
private fun SectionCard(content: @Composable ColumnScope.() -> Unit) {
    Card(
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(Modifier.padding(18.dp), content = content)
    }
}

private typealias ColumnScope = androidx.compose.foundation.layout.ColumnScope

@Composable
private fun CardTitle(text: String) {
    Text(
        text = text.uppercase(),
        style = MaterialTheme.typography.labelMedium,
        color = MaterialTheme.colorScheme.primary,
    )
    Spacer(Modifier.height(12.dp))
}

@Composable
private fun PipelineCard(pipeline: PipelineRunState) {
    SectionCard {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(
                text = "PIPELINE",
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.primary,
            )
            Spacer(Modifier.weight(1f))
            StatusBadge(pipeline.running, pipeline.stage)
        }
        Spacer(Modifier.height(14.dp))

        if (pipeline.running) {
            val total = pipeline.stageTotal
            val processed = pipeline.stageProcessed
            val fraction = if (total > 0) (processed.toFloat() / total).coerceIn(0f, 1f) else 0f
            val animated by animateFloatAsState(targetValue = fraction, label = "progress")

            Text(
                text = stageLabel(pipeline.stage),
                style = MaterialTheme.typography.titleLarge,
                color = MaterialTheme.colorScheme.onSurface,
            )
            Spacer(Modifier.height(10.dp))
            if (total > 0) {
                LinearProgressIndicator(
                    progress = { animated },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(10.dp)
                        .clip(RoundedCornerShape(50)),
                )
                Spacer(Modifier.height(8.dp))
                Row {
                    Text(
                        text = "$processed / $total",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurface,
                    )
                    Spacer(Modifier.weight(1f))
                    Text(
                        text = etaText(pipeline.stageEtaSeconds),
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            } else {
                LinearProgressIndicator(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(10.dp)
                        .clip(RoundedCornerShape(50)),
                )
            }
            Spacer(Modifier.height(14.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(20.dp)) {
                MiniStat("Generated", pipeline.generated)
                MiniStat("Passed", pipeline.passed)
                MiniStat("Rejected", pipeline.rejected)
            }
            pipeline.runElapsedSeconds?.let {
                Spacer(Modifier.height(10.dp))
                Text(
                    text = "Running for ${durationText(it)}",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        } else {
            Text(
                text = "Idle",
                style = MaterialTheme.typography.titleLarge,
                color = MaterialTheme.colorScheme.onSurface,
            )
            Spacer(Modifier.height(4.dp))
            Text(
                text = "No run in progress. Trigger one below.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun StatusBadge(running: Boolean, stage: String) {
    val color = if (running) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.outline
    Row(verticalAlignment = Alignment.CenterVertically) {
        if (running) {
            CircularProgressIndicator(
                modifier = Modifier.size(14.dp),
                strokeWidth = 2.dp,
                color = color,
            )
            Spacer(Modifier.size(8.dp))
        }
        Text(
            text = if (running) "RUNNING" else "IDLE",
            style = MaterialTheme.typography.labelLarge,
            color = color,
        )
    }
}

@Composable
private fun MiniStat(label: String, value: Int) {
    Column {
        Text(
            text = "$value",
            style = MaterialTheme.typography.headlineMedium,
            color = MaterialTheme.colorScheme.onSurface,
        )
        Text(
            text = label.uppercase(),
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

@Composable
private fun FunnelCard(status: AdminStatus) {
    SectionCard {
        CardTitle("Article funnel")
        FunnelRow("New (queued)", status.articles.new)
        FunnelRow("Scored (awaiting generation)", status.articles.scored)
        FunnelRow("Generated", status.articles.generated)
        FunnelRow("Rejected", status.articles.rejected)
        FunnelRow("Duplicate", status.articles.duplicate)
        FunnelRow("Failed", status.articles.failed)
    }
}

@Composable
private fun FunnelRow(label: String, value: Int) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 6.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurface,
        )
        Spacer(Modifier.weight(1f))
        Text(
            text = "$value",
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.onSurface,
            fontFamily = FontFamily.Monospace,
        )
    }
}

@Composable
private fun ContentCard(status: AdminStatus) {
    SectionCard {
        CardTitle("Content")
        FunnelRow("Rabbit holes total", status.totalRabbitHoles)
        FunnelRow("In daily feed", status.feedCount)
        FunnelRow("Feed capacity", status.dailyFeedSize)
    }
}

@Composable
private fun ServerCard(status: AdminStatus) {
    SectionCard {
        CardTitle("Server")
        FunnelTextRow("App", "${status.app} v${status.version}")
        FunnelTextRow("Database", status.database)
        FunnelTextRow("LLM", status.llmProvider)
        FunnelTextRow("Embeddings", status.embeddingProvider)
    }
}

@Composable
private fun FunnelTextRow(label: String, value: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 6.dp),
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurface,
        )
        Spacer(Modifier.weight(1f))
        Text(
            text = value,
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

@Composable
private fun ErrorsCard(errors: List<String>) {
    SectionCard {
        CardTitle("Recent errors")
        errors.takeLast(5).forEach { error ->
            Text(
                text = "• $error",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(vertical = 4.dp),
            )
        }
    }
}

@Composable
private fun ActionButtons(
    inFlight: Boolean,
    onRun: () -> Unit,
    onFetch: () -> Unit,
    onProcess: () -> Unit,
    onRebuild: () -> Unit,
) {
    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        CardTitle("Actions")
        Button(
            onClick = onRun,
            enabled = !inFlight,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("Run full pipeline")
        }
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            OutlinedButton(
                onClick = onFetch,
                enabled = !inFlight,
                modifier = Modifier.weight(1f),
            ) { Text("Fetch RSS") }
            OutlinedButton(
                onClick = onProcess,
                enabled = !inFlight,
                modifier = Modifier.weight(1f),
            ) { Text("Process") }
        }
        OutlinedButton(
            onClick = onRebuild,
            enabled = !inFlight,
            modifier = Modifier.fillMaxWidth(),
            colors = ButtonDefaults.outlinedButtonColors(),
        ) { Text("Rebuild feed") }
        if (inFlight) {
            Box(Modifier.fillMaxWidth().padding(top = 4.dp), contentAlignment = Alignment.Center) {
                CircularProgressIndicator(
                    modifier = Modifier.size(20.dp),
                    strokeWidth = 2.dp,
                )
            }
        }
    }
}

private fun stageLabel(stage: String): String = when (stage) {
    "ingesting" -> "Fetching RSS feeds"
    "scoring" -> "Scoring articles"
    "generating" -> "Generating rabbit holes"
    "rebuilding_feed" -> "Rebuilding daily feed"
    "starting" -> "Starting…"
    "done" -> "Finished"
    else -> stage.replaceFirstChar { it.uppercase() }
}

private fun etaText(etaSeconds: Double?): String {
    if (etaSeconds == null) return "estimating…"
    return "~${durationText(etaSeconds)} left"
}

private fun durationText(seconds: Double): String {
    val total = seconds.toLong()
    val m = total / 60
    val s = total % 60
    return if (m > 0) "${m}m ${s}s" else "${s}s"
}
