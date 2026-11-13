package dev.nfsu2

/** Ponte JNI para o motor C++ (libnfsu2_native.so). */
object NativeBridge {
    init {
        System.loadLibrary("nfsu2_native")
    }

    @JvmStatic external fun nativeSetAssetDir(dir: String)
    @JvmStatic external fun nativeOnSurfaceCreated()
    @JvmStatic external fun nativeOnSurfaceChanged(width: Int, height: Int)
    @JvmStatic external fun nativeOnDrawFrame()
    @JvmStatic external fun nativeOnDrag(dx: Float, dy: Float)
    @JvmStatic external fun nativeStatus(): String
}
