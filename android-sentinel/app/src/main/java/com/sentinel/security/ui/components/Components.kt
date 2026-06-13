package com.sentinel.security.ui.components

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.sentinel.security.core.model.Severity
import com.sentinel.security.ui.theme.SeverityCritical
import com.sentinel.security.ui.theme.SeverityHigh
import com.sentinel.security.ui.theme.SeverityInfo
import com.sentinel.security.ui.theme.SeverityOk
import com.sentinel.security.ui.theme.SeverityWarn

fun severityColor(severity: Severity): Color = when (severity) {
    Severity.OK -> SeverityOk
    Severity.INFO -> SeverityInfo
    Severity.WARN -> SeverityWarn
    Severity.HIGH -> SeverityHigh
    Severity.CRITICAL -> SeverityCritical
}

/** Color for the score ring: higher score = safer = greener. */
private fun scoreColor(score: Int): Color = when {
    score >= 90 -> SeverityOk
    score >= 75 -> SeverityOk
    score >= 55 -> SeverityWarn
    score >= 30 -> SeverityHigh
    else -> SeverityCritical
}

/**
 * Animated Spy Risk Score ring. Shows the numeric score, the posture word, and a sweep proportional
 * to the score. Never relies on color alone — the number + band word carry the meaning too.
 */
@Composable
fun RiskRing(
    score: Int,
    bandLabel: String,
    modifier: Modifier = Modifier,
    subtitle: String? = null,
) {
    val animated by animateFloatAsState(
        targetValue = score.coerceIn(0, 100) / 100f,
        animationSpec = tween(durationMillis = 900),
        label = "riskSweep",
    )
    val ringColor = scoreColor(score)
    val track = MaterialTheme.colorScheme.surfaceVariant

    Box(modifier = modifier.size(220.dp), contentAlignment = Alignment.Center) {
        Canvas(modifier = Modifier.fillMaxWidth().size(220.dp)) {
            val stroke = Stroke(width = 26f, cap = StrokeCap.Round)
            val inset = 26f
            val arcSize = Size(size.width - inset * 2, size.height - inset * 2)
            val topLeft = androidx.compose.ui.geometry.Offset(inset, inset)
            drawArc(
                color = track,
                startAngle = 135f,
                sweepAngle = 270f,
                useCenter = false,
                topLeft = topLeft,
                size = arcSize,
                style = stroke,
            )
            drawArc(
                color = ringColor,
                startAngle = 135f,
                sweepAngle = 270f * animated,
                useCenter = false,
                topLeft = topLeft,
                size = arcSize,
                style = stroke,
            )
        }
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(
                text = score.toString(),
                fontSize = 56.sp,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onSurface,
            )
            Text(
                text = bandLabel,
                fontSize = 16.sp,
                fontWeight = FontWeight.SemiBold,
                color = ringColor,
            )
            if (subtitle != null) {
                Text(
                    text = subtitle,
                    fontSize = 12.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}

@Composable
fun SeverityBadge(severity: Severity, modifier: Modifier = Modifier) {
    val c = severityColor(severity)
    Text(
        text = severity.label,
        color = c,
        fontSize = 12.sp,
        fontWeight = FontWeight.SemiBold,
        modifier = modifier
            .clip(RoundedCornerShape(6.dp))
            .background(c.copy(alpha = 0.14f))
            .border(1.dp, c.copy(alpha = 0.5f), RoundedCornerShape(6.dp))
            .padding(horizontal = 8.dp, vertical = 2.dp),
    )
}

@Composable
fun SectionCard(
    modifier: Modifier = Modifier,
    content: @Composable ColumnScope.() -> Unit,
) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .background(MaterialTheme.colorScheme.surface)
            .border(1.dp, MaterialTheme.colorScheme.outline, RoundedCornerShape(16.dp))
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
        content = content,
    )
}

@Composable
fun LabeledRow(label: String, value: String, valueColor: Color = Color.Unspecified) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Text(label, color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 14.sp)
        Text(
            value,
            color = if (valueColor == Color.Unspecified) MaterialTheme.colorScheme.onSurface else valueColor,
            fontSize = 14.sp,
            fontWeight = FontWeight.Medium,
        )
    }
}
