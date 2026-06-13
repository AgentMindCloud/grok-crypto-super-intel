# ---- Kotlin metadata / annotations ----
-keepattributes *Annotation*, Signature, InnerClasses, EnclosingMethod, RuntimeVisibleAnnotations, AnnotationDefault

# ---- Hilt / Dagger ----
# Hilt ships consumer rules in its AARs; we additionally keep @Inject-constructor classes and
# generated components, which is the common R8 failure mode after AGP upgrades.
-keepclasseswithmembers class * { @javax.inject.Inject <init>(...); }
-keep class * extends dagger.hilt.internal.GeneratedComponent { *; }
-keep,allowobfuscation,allowshrinking @dagger.hilt.android.lifecycle.HiltViewModel class *
-keep class dagger.hilt.** { *; }
-keep class javax.inject.** { *; }

# ---- kotlinx.serialization ----
-keepclassmembers @kotlinx.serialization.Serializable class ** {
    *** Companion;
    *** INSTANCE;
    kotlinx.serialization.KSerializer serializer(...);
}
-keepclasseswithmembers class **$$serializer { *; }

# ---- Room ----
-keep class * extends androidx.room.RoomDatabase { *; }
-keep @androidx.room.Entity class * { *; }

# ---- Shizuku (optional privileged tier; reflection/AIDL bound, class names unstable under R8) ----
# Always set an explicit UserServiceArgs.setTag() in code; these keeps protect the IPC surface.
-keep class moe.shizuku.** { *; }
-keep class rikka.shizuku.** { *; }
-keep interface rikka.shizuku.** { *; }
-keep class * extends android.os.IInterface { *; }
-keepclassmembers class ** implements android.os.IInterface { *; }
