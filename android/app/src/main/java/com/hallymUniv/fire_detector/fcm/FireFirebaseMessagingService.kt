package com.hallymUniv.fire_detector.fcm

import android.util.Log
import com.google.firebase.messaging.FirebaseMessagingService
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import kotlin.concurrent.thread

class FireFirebaseMessagingService : FirebaseMessagingService() {

    override fun onNewToken(token: String) {
        super.onNewToken(token)

        sendTokenToServer(token)
    }

    private fun sendTokenToServer(token: String) {
        val client = OkHttpClient()

        val json = JSONObject().apply {
            put("token", token)
        }

        val body = json.toString()
            .toRequestBody("application/json; charset=utf-8".toMediaType())

        val request = Request.Builder()
            .url("http://api.chaewoon.work/api/v1/register-token")
            .post(body)
            .build()

        thread {
            try {
                client.newCall(request).execute().use { response ->
                    Log.d("FCM", "Token sent: ${response.code}")
                }
            } catch (e: Exception) {
                Log.e("FCM", "Token send failed", e)
            }
        }
    }
}