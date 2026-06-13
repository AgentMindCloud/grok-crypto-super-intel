package com.sentinel.security.ui

import androidx.compose.runtime.Composable
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.sentinel.security.ui.dashboard.DashboardScreen
import com.sentinel.security.ui.log.EventLogScreen
import com.sentinel.security.ui.settings.SettingsScreen

private object Routes {
    const val DASHBOARD = "dashboard"
    const val LOG = "log"
    const val SETTINGS = "settings"
}

@Composable
fun MainNav() {
    val nav = rememberNavController()
    NavHost(navController = nav, startDestination = Routes.DASHBOARD) {
        composable(Routes.DASHBOARD) {
            DashboardScreen(
                onOpenLog = { nav.navigate(Routes.LOG) },
                onOpenSettings = { nav.navigate(Routes.SETTINGS) },
            )
        }
        composable(Routes.LOG) {
            EventLogScreen(onBack = { nav.popBackStack() })
        }
        composable(Routes.SETTINGS) {
            SettingsScreen(onBack = { nav.popBackStack() })
        }
    }
}
