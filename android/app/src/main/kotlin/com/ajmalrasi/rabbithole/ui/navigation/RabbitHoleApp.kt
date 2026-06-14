package com.ajmalrasi.rabbithole.ui.navigation

import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.ajmalrasi.rabbithole.ui.admin.AdminScreen
import com.ajmalrasi.rabbithole.ui.categories.CategoriesScreen
import com.ajmalrasi.rabbithole.ui.categories.CategoryItemsScreen
import com.ajmalrasi.rabbithole.ui.detail.DetailScreen
import com.ajmalrasi.rabbithole.ui.favorites.FavoritesScreen
import com.ajmalrasi.rabbithole.ui.feed.FeedScreen
import com.ajmalrasi.rabbithole.ui.search.SearchScreen
import com.ajmalrasi.rabbithole.ui.settings.SettingsScreen
import java.net.URLEncoder

@Composable
fun RabbitHoleApp() {
    val navController = rememberNavController()
    val backStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = backStackEntry?.destination?.route
    val showBottomBar = TopLevelDestination.entries.any { it.route == currentRoute }

    Scaffold(
        bottomBar = {
            if (showBottomBar) {
                NavigationBar(containerColor = MaterialTheme.colorScheme.surface) {
                    val currentDestination = backStackEntry?.destination
                    TopLevelDestination.entries.forEach { destination ->
                        val selected = currentDestination?.hierarchy?.any { it.route == destination.route } == true
                        NavigationBarItem(
                            selected = selected,
                            onClick = {
                                navController.navigate(destination.route) {
                                    popUpTo(navController.graph.findStartDestination().id) {
                                        saveState = true
                                    }
                                    launchSingleTop = true
                                    restoreState = true
                                }
                            },
                            icon = { Icon(destination.icon, contentDescription = destination.label) },
                            label = { Text(destination.label) },
                        )
                    }
                }
            }
        },
    ) { padding ->
        NavHost(
            navController = navController,
            startDestination = Routes.FEED,
            modifier = Modifier.padding(padding),
        ) {
            composable(Routes.FEED) {
                FeedScreen(onItemClick = { navController.navigate(Routes.detail(it)) })
            }
            composable(Routes.SEARCH) {
                SearchScreen(onItemClick = { navController.navigate(Routes.detail(it)) })
            }
            composable(Routes.CATEGORIES) {
                CategoriesScreen(
                    onCategoryClick = { name ->
                        val encoded = URLEncoder.encode(name, "UTF-8")
                        navController.navigate(Routes.categoryItems(encoded))
                    },
                )
            }
            composable(Routes.FAVORITES) {
                FavoritesScreen(onItemClick = { navController.navigate(Routes.detail(it)) })
            }
            composable(Routes.SETTINGS) {
                SettingsScreen(onOpenAdmin = { navController.navigate(Routes.ADMIN) })
            }
            composable(Routes.ADMIN) {
                AdminScreen(onBack = { navController.popBackStack() })
            }
            composable(Routes.DETAIL) {
                DetailScreen(onBack = { navController.popBackStack() })
            }
            composable(Routes.CATEGORY_ITEMS) {
                CategoryItemsScreen(
                    onBack = { navController.popBackStack() },
                    onItemClick = { navController.navigate(Routes.detail(it)) },
                )
            }
        }
    }
}
