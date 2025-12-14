package com.hallymUniv.fire_detector.ui.icons

import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.graphics.vector.path
import androidx.compose.ui.unit.dp

val Fire: ImageVector
    get() {
        if (_Fire != null) return _Fire!!

        _Fire = ImageVector.Builder(
            name = "Fire",
            defaultWidth = 24.dp,
            defaultHeight = 24.dp,
            viewportWidth = 24f,
            viewportHeight = 24f
        ).apply {
            path(
                stroke = SolidColor(Color(0xFF0F172A)),
                strokeLineWidth = 1.5f,
                strokeLineCap = StrokeCap.Round,
                strokeLineJoin = StrokeJoin.Round
            ) {
                moveTo(15.3622f, 5.21361f)
                curveTo(18.2427f, 6.50069f, 20.25f, 9.39075f, 20.25f, 12.7497f)
                curveTo(20.25f, 17.306f, 16.5563f, 20.9997f, 12f, 20.9997f)
                curveTo(7.44365f, 20.9997f, 3.75f, 17.306f, 3.75f, 12.7497f)
                curveTo(3.75f, 10.5376f, 4.62058f, 8.52889f, 6.03781f, 7.04746f)
                curveTo(6.8043f, 8.11787f, 7.82048f, 8.99731f, 9.00121f, 9.60064f)
                curveTo(9.04632f, 6.82497f, 10.348f, 4.35478f, 12.3621f, 2.73413f)
                curveTo(13.1255f, 3.75788f, 14.1379f, 4.61821f, 15.3622f, 5.21361f)
                close()
            }
            path(
                stroke = SolidColor(Color(0xFF0F172A)),
                strokeLineWidth = 1.5f,
                strokeLineCap = StrokeCap.Round,
                strokeLineJoin = StrokeJoin.Round
            ) {
                moveTo(12f, 18f)
                curveTo(14.0711f, 18f, 15.75f, 16.3211f, 15.75f, 14.25f)
                curveTo(15.75f, 12.3467f, 14.3321f, 10.7746f, 12.4949f, 10.5324f)
                curveTo(11.4866f, 11.437f, 10.7862f, 12.6779f, 10.5703f, 14.0787f)
                curveTo(9.78769f, 13.8874f, 9.06529f, 13.5425f, 8.43682f, 13.0779f)
                curveTo(8.31559f, 13.4467f, 8.25f, 13.8407f, 8.25f, 14.25f)
                curveTo(8.25f, 16.3211f, 9.92893f, 18f, 12f, 18f)
                close()
            }
        }.build()

        return _Fire!!
    }

private var _Fire: ImageVector? = null