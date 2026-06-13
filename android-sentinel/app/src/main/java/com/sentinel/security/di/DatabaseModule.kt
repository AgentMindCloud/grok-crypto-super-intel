package com.sentinel.security.di

import android.content.Context
import androidx.room.Room
import com.sentinel.security.data.db.EventLogDao
import com.sentinel.security.data.db.ScanDao
import com.sentinel.security.data.db.SentinelDatabase
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    @Suppress("DEPRECATION")
    fun provideDatabase(@ApplicationContext context: Context): SentinelDatabase =
        Room.databaseBuilder(context, SentinelDatabase::class.java, SentinelDatabase.NAME)
            .fallbackToDestructiveMigration()
            .build()

    @Provides
    fun provideScanDao(db: SentinelDatabase): ScanDao = db.scanDao()

    @Provides
    fun provideEventLogDao(db: SentinelDatabase): EventLogDao = db.eventLogDao()
}
