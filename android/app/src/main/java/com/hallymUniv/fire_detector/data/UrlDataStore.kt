package com.hallymUniv.fire_detector.data

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.dataStore by preferencesDataStore(name = "settings")

object UrlDataStore {

    private val DASHBOARD_URL = stringPreferencesKey("dashboard_url")

    fun getUrl(context: Context): Flow<String?> =
        context.dataStore.data.map { prefs ->
            prefs[DASHBOARD_URL]
        }

    suspend fun saveUrl(context: Context, url: String) {
        context.dataStore.edit { prefs ->
            prefs[DASHBOARD_URL] = url
        }
    }
}