package com.example.fire_detector

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.example.fire_detector.ui.dashboard.DashboardScreen
import com.example.fire_detector.ui.theme.Fire_detectorTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContent {
            Fire_detectorTheme {
                DashboardScreen(
                    dashboardUrl = "https://www.google.com",
                    onAlarmClick = { println("알림 클릭") },
                    onSettingClick = { println("설정 클릭") }
                )
            }
        }
    }
}