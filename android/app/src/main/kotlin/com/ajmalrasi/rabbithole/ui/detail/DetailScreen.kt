package com.ajmalrasi.rabbithole.ui.detail

import android.content.Intent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Bookmark
import androidx.compose.material.icons.automirrored.outlined.OpenInNew
import androidx.compose.material.icons.outlined.BookmarkBorder
import androidx.compose.material.icons.outlined.Psychology
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.core.net.toUri
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.ajmalrasi.rabbithole.domain.model.RabbitHoleDetail
import com.ajmalrasi.rabbithole.ui.common.CategoryTag
import com.ajmalrasi.rabbithole.ui.common.ErrorState
import com.ajmalrasi.rabbithole.ui.common.LoadingState
import com.ajmalrasi.rabbithole.ui.common.ScorePill
import com.ajmalrasi.rabbithole.ui.common.UiState
import com.ajmalrasi.rabbithole.util.ChatGptLauncher

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DetailScreen(
    onBack: () -> Unit,
    viewModel: DetailViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    val askState by viewModel.askState.collectAsStateWithLifecycle()
    val isFavorite by viewModel.isFavorite.collectAsStateWithLifecycle()

    Scaffold(
        topBar = {
            TopAppBar(
                title = {},
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    IconButton(onClick = viewModel::toggleFavorite) {
                        Icon(
                            imageVector = if (isFavorite) Icons.Filled.Bookmark else Icons.Outlined.BookmarkBorder,
                            contentDescription = if (isFavorite) "Remove from saved" else "Save",
                            tint = if (isFavorite) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface,
                        )
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
            is UiState.Success -> DetailContent(
                detail = s.data,
                askState = askState,
                onQuestionChange = viewModel::onQuestionChange,
                onLaunchError = viewModel::reportLaunchError,
                modifier = Modifier.padding(padding),
            )
        }
    }
}

@Composable
private fun DetailContent(
    detail: RabbitHoleDetail,
    askState: AskUiState,
    onQuestionChange: (String) -> Unit,
    onLaunchError: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    Column(
        modifier = modifier
            .fillMaxWidth()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp)
            .padding(bottom = 40.dp),
    ) {
        CategoryTag(detail.category)
        Spacer(Modifier.height(10.dp))
        Text(
            text = detail.title,
            style = MaterialTheme.typography.displaySmall,
            color = MaterialTheme.colorScheme.onBackground,
        )
        Spacer(Modifier.height(12.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            ScorePill("CURIOSITY", detail.curiosityScore)
            ScorePill("HIDDEN", detail.hiddenMechanismScore)
        }
        Spacer(Modifier.height(24.dp))

        Section("The observation", detail.observation)
        QuestionBlock(detail.question)
        Section("The hidden mechanism", detail.hiddenMechanism)
        Section("How it works", detail.explanation)
        Section("Interesting fact", detail.interestingFact)
        Section("Why it matters", detail.whyItMatters)
        QuestionBlock(detail.followUpQuestion, label = "Go deeper")

        if (detail.sourceUrl.isNotBlank()) {
            Spacer(Modifier.height(20.dp))
            OutlinedButton(
                onClick = {
                    runCatching {
                        context.startActivity(Intent(Intent.ACTION_VIEW, detail.sourceUrl.toUri()))
                    }
                },
                shape = RoundedCornerShape(12.dp),
            ) {
                Icon(Icons.AutoMirrored.Outlined.OpenInNew, contentDescription = null)
                Spacer(Modifier.height(0.dp))
                Text("  Read the source", style = MaterialTheme.typography.labelLarge)
            }
        }

        Spacer(Modifier.height(28.dp))
        AskSection(
            detail = detail,
            askState = askState,
            onQuestionChange = onQuestionChange,
            onLaunchError = onLaunchError,
        )
    }
}

@Composable
private fun AskSection(
    detail: RabbitHoleDetail,
    askState: AskUiState,
    onQuestionChange: (String) -> Unit,
    onLaunchError: (String) -> Unit,
) {
    val context = LocalContext.current
    val hasChatGpt = remember { ChatGptLauncher.isChatGptInstalled(context) }

    Card(
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(Modifier.padding(18.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    Icons.Outlined.Psychology,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary,
                )
                Spacer(Modifier.size(10.dp))
                Text(
                    text = "Ask ChatGPT",
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onSurface,
                )
            }
            Spacer(Modifier.height(4.dp))
            Text(
                text = if (hasChatGpt) {
                    "Pre-filled with a short prompt from the article — edit before sending"
                } else {
                    "Pre-filled with a short prompt from the article — opens in your browser"
                },
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(Modifier.height(14.dp))
            OutlinedTextField(
                value = askState.question,
                onValueChange = onQuestionChange,
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Prompt for ChatGPT") },
                minLines = 4,
                maxLines = 10,
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Go),
                keyboardActions = KeyboardActions(onGo = {
                    if (askState.question.isNotBlank()) {
                        val ok = ChatGptLauncher.open(context, detail, askState.question)
                        if (!ok) onLaunchError("Couldn't open ChatGPT. Install the app or a browser.")
                    }
                }),
            )
            Spacer(Modifier.height(12.dp))
            Button(
                onClick = {
                    val ok = ChatGptLauncher.open(context, detail, askState.question)
                    if (!ok) {
                        onLaunchError("Couldn't open ChatGPT. Install the app or a browser.")
                    }
                },
                enabled = askState.question.isNotBlank(),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(if (hasChatGpt) "Open in ChatGPT" else "Open in browser")
            }
            askState.launchError?.let { error ->
                Spacer(Modifier.height(10.dp))
                Text(
                    text = error,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.error,
                )
            }
        }
    }
}

@Composable
private fun Section(title: String, body: String) {
    if (body.isBlank()) return
    Spacer(Modifier.height(20.dp))
    Text(
        text = title.uppercase(),
        style = MaterialTheme.typography.labelMedium,
        color = MaterialTheme.colorScheme.primary,
    )
    Spacer(Modifier.height(6.dp))
    Text(
        text = body,
        style = MaterialTheme.typography.bodyLarge,
        color = MaterialTheme.colorScheme.onBackground,
    )
}

@Composable
private fun QuestionBlock(text: String, label: String = "The question") {
    if (text.isBlank()) return
    Spacer(Modifier.height(24.dp))
    Text(
        text = label.uppercase(),
        style = MaterialTheme.typography.labelMedium,
        color = MaterialTheme.colorScheme.primary,
    )
    Spacer(Modifier.height(6.dp))
    Text(
        text = text,
        style = MaterialTheme.typography.headlineMedium.copy(fontStyle = FontStyle.Italic),
        color = MaterialTheme.colorScheme.onBackground,
    )
}
