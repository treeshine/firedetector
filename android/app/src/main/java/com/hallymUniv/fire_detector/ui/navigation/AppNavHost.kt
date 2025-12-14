package com.hallymUniv.fire_detector.ui.navigation

import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.hallymUniv.fire_detector.data.UrlDataStore
import com.hallymUniv.fire_detector.ui.dashboard.DashboardScreen
import com.hallymUniv.fire_detector.ui.setup.UrlSetupScreen
import com.hallymUniv.fire_detector.ui.splash.SplashScreen
import com.hallymUniv.fire_detector.ui.alarm.AlarmScreen
import com.hallymUniv.fire_detector.ui.alarm.AlarmItem
import kotlinx.coroutines.launch

sealed class Route(val route: String) {
    object Splash : Route("splash")
    object Setup : Route("setup")
    object Dashboard : Route("dashboard")
    object  Alarm : Route("alarm")
}

@Composable
fun AppNavHost(
    modifier: Modifier = Modifier
) {
    val navController = rememberNavController()
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    val savedUrl by UrlDataStore
        .getUrl(context)
        .collectAsState(initial = null)

    NavHost(
        navController = navController,
        startDestination = Route.Splash.route,
        modifier = modifier
    ) {

        // Splash
        composable(Route.Splash.route) {
            SplashScreen(
                onResult = { _ ->
                    navController.navigate(
                        if (savedUrl.isNullOrBlank())
                            Route.Setup.route
                        else
                            Route.Dashboard.route
                    ) {
                        popUpTo(Route.Splash.route) { inclusive = true }
                    }
                }
            )
        }

        // URL 설정 (초기 + 설정 공용)
        composable(Route.Setup.route) {
            UrlSetupScreen(
                initialUrl = savedUrl ?: "",
                showBackButton = !savedUrl.isNullOrBlank(),
                onSave = { url ->
                    scope.launch {
                        UrlDataStore.saveUrl(context, url)
                        navController.navigate(Route.Dashboard.route) {
                            popUpTo(Route.Setup.route) { inclusive = true }
                        }
                    }
                },
                onBack = {
                    navController.popBackStack()
                }
            )
        }

        // Dashboard (WebView)
        composable(Route.Dashboard.route) {
            DashboardScreen(
                dashboardUrl = savedUrl ?: "",
                onAlarmClick = {
                    navController.navigate(Route.Alarm.route)
                },
                onSettingClick = {
                    navController.navigate(Route.Setup.route)
                }
            )
        }

        // Alarm 화면
        composable(Route.Alarm.route) {
            // 지금은 더미 데이터
            val alarms = listOf(
                AlarmItem(
                    id = 1,
                    title = "화재 감지",
                    message = "화재가 감지되었습니다.",
                    time = "2024-12-12 14:23"
                )
            )

            AlarmScreen(
                alarms = alarms,
                onClose = { navController.popBackStack() },
                onAlarmClick = {
                    navController.navigate(Route.Dashboard.route) {
                        popUpTo(Route.Alarm.route) { inclusive = true }
                    }
                }
            )
        }
    }
}