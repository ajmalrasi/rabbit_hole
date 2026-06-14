package com.ajmalrasi.rabbithole.util

import android.app.Activity
import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.net.Uri
import com.ajmalrasi.rabbithole.domain.model.RabbitHoleDetail

/**
 * Opens ChatGPT with a pre-filled prompt.
 *
 * The official Android app does not expose a public intent for pre-filling text,
 * but it often registers as a handler for chatgpt.com links. We try the app
 * package first, then fall back to the default browser — both use
 * ``?q=...&temporary-chat=true`` which pre-fills a new temporary chat on the web.
 */
object ChatGptLauncher {

    private const val CHATGPT_PACKAGE = "com.openai.chatgpt"
    private const val BASE_URL = "https://chatgpt.com/"

    /** Max chars per article snippet so the prompt stays URL-friendly. */
    private const val SNIPPET_MAX = 140

    /**
     * A concise, article-grounded prompt — enough context to answer well, short enough for URLs.
     */
    fun buildDefaultPrompt(detail: RabbitHoleDetail): String = buildString {
        val observation = detail.observation.trim()
        val question = detail.question.trim()
        val mechanism = detail.hiddenMechanism.trim()
        val followUp = detail.followUpQuestion.trim().ifBlank { question }

        appendLine("Article: \"${detail.title}\" (${detail.category})")
        appendLine()

        val context = listOfNotNull(
            observation.takeIf { it.isNotBlank() }?.let { "Observation: ${truncate(it)}" },
            mechanism.takeIf { it.isNotBlank() }?.let { "Hidden mechanism: ${truncate(it)}" },
        ).joinToString("\n")
        if (context.isNotBlank()) {
            appendLine(context)
            appendLine()
        }

        if (question.isNotBlank() && question != followUp) {
            appendLine("Core question: $question")
            appendLine()
        }

        append("Go deeper: $followUp ")
        append(
            "Explain the underlying system step by step, use a simple analogy, " +
                "and tell me what most people misunderstand.",
        )
    }.trim()

    private fun truncate(text: String): String =
        if (text.length <= SNIPPET_MAX) text else text.take(SNIPPET_MAX).trimEnd() + "…"

    /** Text sent to ChatGPT — uses the field content, or the rich default if empty. */
    fun buildPrompt(detail: RabbitHoleDetail, userQuestion: String): String {
        val question = userQuestion.trim()
        return question.ifBlank { buildDefaultPrompt(detail) }
    }

    /** Browsers can choke on very long query strings — keep a safe ceiling. */
    private const val MAX_PROMPT_CHARS = 2_000

    fun buildUri(prompt: String): Uri {
        val trimmed = if (prompt.length > MAX_PROMPT_CHARS) {
            prompt.take(MAX_PROMPT_CHARS).trimEnd() +
                "\n\n[Prompt trimmed for URL length — edit or paste the rest in ChatGPT if needed.]"
        } else {
            prompt
        }
        return Uri.parse(BASE_URL).buildUpon()
            .appendQueryParameter("q", trimmed)
            .appendQueryParameter("temporary-chat", "true")
            .build()
    }

    /** @return true if an activity was started */
    fun open(context: Context, detail: RabbitHoleDetail, userQuestion: String): Boolean {
        val uri = buildUri(buildPrompt(detail, userQuestion))

        // Try ChatGPT app first (handles chatgpt.com links on many devices).
        if (tryStartActivity(context, Intent(Intent.ACTION_VIEW, uri).apply {
            setPackage(CHATGPT_PACKAGE)
        })) {
            return true
        }

        // Any installed browser.
        if (tryStartActivity(context, Intent(Intent.ACTION_VIEW, uri))) {
            return true
        }

        // Chooser as a last resort — avoids false negatives from resolveActivity on Android 11+.
        val chooser = Intent.createChooser(
            Intent(Intent.ACTION_VIEW, uri),
            "Open ChatGPT",
        )
        return tryStartActivity(context, chooser)
    }

    private fun tryStartActivity(context: Context, intent: Intent): Boolean {
        return try {
            if (context !is Activity) {
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            context.startActivity(intent)
            true
        } catch (_: ActivityNotFoundException) {
            false
        }
    }

    fun isChatGptInstalled(context: Context): Boolean =
        context.packageManager.getLaunchIntentForPackage(CHATGPT_PACKAGE) != null
}
