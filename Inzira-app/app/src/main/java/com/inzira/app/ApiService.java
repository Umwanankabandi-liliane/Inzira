package com.inzira.app;

import retrofit2.Call;
import retrofit2.http.Body;
import retrofit2.http.DELETE;
import retrofit2.http.GET;
import retrofit2.http.POST;
import retrofit2.http.PUT;
import retrofit2.http.Path;
import java.util.Map;

public interface ApiService {

    @GET("health")
    Call<HealthResponse> health();

    @POST("search")
    Call<SearchResponse> search(@Body SearchRequest request);

    @POST("assistant")
    Call<AssistantResponse> assistant(@Body AssistantRequest request);

    @GET("youth/radar")
    Call<YouthRadarResponse> youthRadar();

    @GET("registry/opportunities")
    Call<RegistryOpportunitiesResponse> registryOpportunities(
            @retrofit2.http.Query("limit") int limit,
            @retrofit2.http.Query("category") String category,
            @retrofit2.http.Query("district") String district,
            @retrofit2.http.Query("q") String query);

    @POST("youth/matches")
    Call<MatchesResponse> youthMatches(@Body YouthProfileRequest profile);

    @GET("mifotra/staff-config")
    Call<MifotraStaffConfigResponse> mifotraStaffConfig();

    @POST("mifotra/verify-staff")
    Call<MifotraPinResponse> verifyMifotraStaff(@Body MifotraStaffRequest request);

    @GET("mifotra/dashboard")
    Call<MifotraDashboardResponse> mifotraDashboard(
            @retrofit2.http.Query("days") int days,
            @retrofit2.http.Header("X-Mifotra-Token") String token);

    @POST("me/saved")
    Call<Map<String, Object>> saveSite(@Body SavedSiteBody body);

    @DELETE("me/saved/{domain}")
    Call<Map<String, Object>> removeSite(@Path("domain") String domain);

    @PUT("me/saved/{domain}/notify")
    Call<Map<String, Object>> toggleNotify(@Path("domain") String domain, @Body NotifyBody body);

    @POST("me/push/fcm")
    Call<Map<String, Object>> registerFcm(@Body FcmTokenBody body);
}