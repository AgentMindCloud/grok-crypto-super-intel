package com.sentinel.security.di

import com.sentinel.security.core.scan.Detector
import com.sentinel.security.feature.appscan.AppScanner
import dagger.Binds
import dagger.Module
import dagger.multibindings.IntoSet
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent

/**
 * Detectors are contributed into a multibound Set so the [com.sentinel.security.core.scan.ScanRunner]
 * runs all of them without knowing the concrete list. New detectors just add an @IntoSet binding.
 */
@Module
@InstallIn(SingletonComponent::class)
abstract class DetectorModule {

    @Binds
    @IntoSet
    abstract fun bindAppScanner(impl: AppScanner): Detector
}
