package com.ajmalrasi.rabbithole.ui.navigation

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Bookmarks
import androidx.compose.material.icons.outlined.Category
import androidx.compose.material.icons.outlined.Explore
import androidx.compose.material.icons.outlined.Search
import androidx.compose.material.icons.outlined.Settings
import androidx.compose.ui.graphics.vector.ImageVector

object Routes {
    const val FEED = "feed"
    const val SEARCH = "search"
    const val CATEGORIES = "categories"
    const val FAVORITES = "favorites"
    const val SETTINGS = "settings"
    const val ADMIN = "admin"
    const val DETAIL = "detail/{id}"
    const val CATEGORY_ITEMS = "category/{name}"

    fun detail(id: Int) = "detail/$id"
    fun categoryItems(name: String) = "category/$name"
}

enum class TopLevelDestination(
    val route: String,
    val label: String,
    val icon: ImageVector,
) {
    FEED(Routes.FEED, "Feed", Icons.Outlined.Explore),
    SEARCH(Routes.SEARCH, "Search", Icons.Outlined.Search),
    CATEGORIES(Routes.CATEGORIES, "Topics", Icons.Outlined.Category),
    FAVORITES(Routes.FAVORITES, "Saved", Icons.Outlined.Bookmarks),
    SETTINGS(Routes.SETTINGS, "Settings", Icons.Outlined.Settings),
}
