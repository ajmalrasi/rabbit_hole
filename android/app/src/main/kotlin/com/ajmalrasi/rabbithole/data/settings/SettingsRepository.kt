package com.ajmalrasi.rabbithole.data.settings

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.ajmalrasi.rabbithole.BuildConfig
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

private val Context.dataStore by preferencesDataStore(name = "rabbit_hole_settings")

/** Default feed filter on first launch — user can switch to All or other topics. */
const val DEFAULT_PREFERRED_CATEGORY = "engineering"

@Singleton
class SettingsRepository @Inject constructor(
    @ApplicationContext private val context: Context,
) {
    private val apiBaseUrlKey = stringPreferencesKey("api_base_url")
    private val preferredCategoryKey = stringPreferencesKey("preferred_feed_category")

    val apiBaseUrl: Flow<String> = context.dataStore.data.map { prefs ->
        prefs[apiBaseUrlKey] ?: BuildConfig.API_BASE_URL
    }

    /** null means "All categories". Unset defaults to engineering. */
    val preferredFeedCategory: Flow<String?> = context.dataStore.data.map { prefs ->
        when {
            !prefs.contains(preferredCategoryKey) -> DEFAULT_PREFERRED_CATEGORY
            else -> prefs[preferredCategoryKey]
        }
    }

    suspend fun preferredFeedCategoryOnce(): String? = preferredFeedCategory.first()

    suspend fun setApiBaseUrl(url: String) {
        context.dataStore.edit { prefs ->
            prefs[apiBaseUrlKey] = url.trim().trimEnd('/')
        }
    }

    suspend fun setPreferredFeedCategory(category: String?) {
        context.dataStore.edit { prefs ->
            if (category == null) {
                prefs[preferredCategoryKey] = ""
            } else {
                prefs[preferredCategoryKey] = category
            }
        }
    }
}
