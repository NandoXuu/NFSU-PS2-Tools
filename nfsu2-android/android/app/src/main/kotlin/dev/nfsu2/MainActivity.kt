package dev.nfsu2

import android.app.Activity
import android.graphics.Color
import android.opengl.GLSurfaceView
import android.os.Bundle
import android.view.MotionEvent
import android.view.ViewGroup
import android.widget.FrameLayout
import android.widget.TextView
import javax.microedition.khronos.egl.EGLConfig
import javax.microedition.khronos.opengles.GL10

/**
 * Modo de diagnóstico: carrega <externalFilesDir>/diag/car.nmsh e renderiza.
 * Arraste na tela para girar o veículo. O texto no topo mostra o resultado da carga.
 */
class MainActivity : Activity() {
    private lateinit var glView: GLSurfaceView
    private lateinit var statusView: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val dir = getExternalFilesDir(null)?.absolutePath ?: filesDir.absolutePath
        NativeBridge.nativeSetAssetDir(dir)

        glView = object : GLSurfaceView(this) {
            private var lx = 0f
            private var ly = 0f
            override fun onTouchEvent(e: MotionEvent): Boolean {
                when (e.actionMasked) {
                    MotionEvent.ACTION_DOWN -> { lx = e.x; ly = e.y }
                    MotionEvent.ACTION_MOVE -> {
                        val dx = e.x - lx
                        val dy = e.y - ly
                        lx = e.x; ly = e.y
                        queueEvent { NativeBridge.nativeOnDrag(dx, dy) }
                    }
                }
                return true
            }
        }.apply {
            setEGLContextClientVersion(3)
            setRenderer(object : GLSurfaceView.Renderer {
                override fun onSurfaceCreated(gl: GL10?, config: EGLConfig?) {
                    NativeBridge.nativeOnSurfaceCreated()
                    runOnUiThread { statusView.text = NativeBridge.nativeStatus() }
                }
                override fun onSurfaceChanged(gl: GL10?, w: Int, h: Int) =
                    NativeBridge.nativeOnSurfaceChanged(w, h)
                override fun onDrawFrame(gl: GL10?) = NativeBridge.nativeOnDrawFrame()
            })
            renderMode = GLSurfaceView.RENDERMODE_CONTINUOUSLY
        }

        statusView = TextView(this).apply {
            setTextColor(Color.WHITE)
            setBackgroundColor(0x88000000.toInt())
            textSize = 12f
            setPadding(16, 8, 16, 8)
            text = "diagnostico: iniciando..."
        }

        val root = FrameLayout(this)
        root.addView(glView, ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT)
        root.addView(statusView, FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT))
        setContentView(root)
    }

    override fun onResume() { super.onResume(); glView.onResume() }
    override fun onPause() { glView.onPause(); super.onPause() }
}
