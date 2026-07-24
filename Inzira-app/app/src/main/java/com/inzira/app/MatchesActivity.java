package com.inzira.app;

import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.ProgressBar;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import com.google.android.material.bottomnavigation.BottomNavigationView;
import com.google.android.material.chip.Chip;
import com.google.android.material.chip.ChipGroup;
import com.google.firebase.database.FirebaseDatabase;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class MatchesActivity extends AppCompatActivity {

    private Spinner spDistrict;
    private Spinner spAge;
    private Spinner spEducation;
    private ChipGroup chipGroupInterests;
    private ProgressBar progressMatches;
    private RecyclerView recyclerMatches;
    private TextView tvNoMatches;
    private TextView tvProfileScore;
    private TextView tvProfileScoreLabel;
    private TextView tvInsights;
    private ProgressBar profileProgressBar;
    private View profileProgressCard;
    private View matchesHeader;
    private final List<OpportunityResult> matchResults = new ArrayList<>();
    private MatchAdapter adapter;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        if (!SessionManager.isLoggedIn(this)) {
            NavHelper.openLogin(this, false, false);
            finish();
            return;
        }

        setContentView(R.layout.activity_matches);

        spDistrict = findViewById(R.id.spDistrict);
        spAge = findViewById(R.id.spAge);
        spEducation = findViewById(R.id.spEducation);
        chipGroupInterests = findViewById(R.id.chipGroupInterests);
        progressMatches = findViewById(R.id.progressMatches);
        recyclerMatches = findViewById(R.id.recyclerMatches);
        tvNoMatches = findViewById(R.id.tvNoMatches);
        tvProfileScore = findViewById(R.id.tvProfileScore);
        tvProfileScoreLabel = findViewById(R.id.tvProfileScoreLabel);
        tvInsights = findViewById(R.id.tvInsights);
        profileProgressBar = findViewById(R.id.profileProgressBar);
        profileProgressCard = findViewById(R.id.profileProgressCard);
        matchesHeader = findViewById(R.id.matchesHeader);
        Button btnSaveProfile = findViewById(R.id.btnSaveProfile);
        BottomNavigationView bottomNav = findViewById(R.id.bottomNav);

        DistrictHelper.setupSpinner(this, spDistrict);
        AgeHelper.setupSpinner(this, spAge);
        EducationHelper.setupSpinner(this, spEducation);
        setupInterestChips();
        loadSavedProfile();
        applyLanguageUi();

        adapter = new MatchAdapter(matchResults, this);
        recyclerMatches.setLayoutManager(new LinearLayoutManager(this));
        recyclerMatches.setAdapter(adapter);

        btnSaveProfile.setOnClickListener(v -> saveProfileAndFetchMatches());
        NavHelper.wireBottomNav(this, bottomNav, R.id.navMatches);

        if (InziraPrefs.isProfileComplete(this)) {
            fetchMatches();
        }
    }

    private void setupInterestChips() {
        String[] interests = getResources().getStringArray(R.array.interest_fields);
        chipGroupInterests.removeAllViews();
        for (int i = 1; i < interests.length; i++) {
            Chip chip = new Chip(this);
            chip.setText(interests[i]);
            chip.setCheckable(true);
            chip.setChipBackgroundColorResource(R.color.badge_blue_background);
            chip.setTextColor(getColor(R.color.badge_blue_text));
            chip.setChipStrokeWidth(0);
            chipGroupInterests.addView(chip);
        }
    }

    private void loadSavedProfile() {
        String district = InziraPrefs.getDistrict(this);
        if (district != null && !district.isEmpty()) {
            DistrictHelper.selectDistrict(spDistrict, district);
        }
        String age = InziraPrefs.getAge(this);
        if (age != null && !age.isEmpty()) {
            AgeHelper.selectAge(spAge, age);
        }
        String education = InziraPrefs.getEducation(this);
        if (education != null && !education.isEmpty()) {
            EducationHelper.selectEducation(spEducation, education);
        }
        String savedInterests = InziraPrefs.getInterests(this);
        if (savedInterests != null && !savedInterests.isEmpty()) {
            Set<String> selected = new HashSet<>(Arrays.asList(savedInterests.split(",")));
            for (int i = 0; i < chipGroupInterests.getChildCount(); i++) {
                View child = chipGroupInterests.getChildAt(i);
                if (child instanceof Chip) {
                    Chip chip = (Chip) child;
                    chip.setChecked(selected.contains(chip.getText().toString().trim()));
                }
            }
        }
    }

    private List<String> selectedInterests() {
        List<String> list = new ArrayList<>();
        for (int i = 0; i < chipGroupInterests.getChildCount(); i++) {
            View child = chipGroupInterests.getChildAt(i);
            if (child instanceof Chip) {
                Chip chip = (Chip) child;
                if (chip.isChecked()) {
                    list.add(chip.getText().toString().trim());
                }
            }
        }
        return list;
    }

    private void saveProfileAndFetchMatches() {
        String district = DistrictHelper.selectedDistrict(spDistrict);
        String age = AgeHelper.selectedAge(spAge);
        String education = EducationHelper.selectedEducation(spEducation);
        List<String> interests = selectedInterests();

        if (district.isEmpty()) {
            Toast.makeText(this, LanguageHelper.selectDistrictToast(this), Toast.LENGTH_SHORT).show();
            return;
        }
        if (age.isEmpty()) {
            Toast.makeText(this, LanguageHelper.selectAgeToast(this), Toast.LENGTH_SHORT).show();
            return;
        }
        if (education.isEmpty()) {
            Toast.makeText(this, LanguageHelper.selectEducationToast(this), Toast.LENGTH_SHORT).show();
            return;
        }
        if (interests.isEmpty()) {
            Toast.makeText(this, LanguageHelper.selectInterestsToast(this), Toast.LENGTH_SHORT).show();
            return;
        }

        InziraPrefs.setDistrict(this, district);
        InziraPrefs.setAge(this, age);
        InziraPrefs.setEducation(this, education);
        InziraPrefs.setInterests(this, String.join(",", interests));
        InziraPrefs.setProfileComplete(this, true);
        syncProfileToFirebase(district, age, education, interests);
        fetchMatches();
    }

    private void syncProfileToFirebase(String district, String age, String education, List<String> interests) {
        if (FirebaseUtil.currentUser() == null) {
            return;
        }
        java.util.Map<String, Object> updates = new java.util.HashMap<>();
        updates.put("district", district);
        updates.put("age", age);
        updates.put("education", education);
        updates.put("interests", interests);
        FirebaseDatabase.getInstance()
                .getReference("users")
                .child(FirebaseUtil.currentUser().getUid())
                .updateChildren(updates);
    }

    private void fetchMatches() {
        progressMatches.setVisibility(View.VISIBLE);
        recyclerMatches.setVisibility(View.GONE);
        matchesHeader.setVisibility(View.GONE);
        tvNoMatches.setVisibility(View.GONE);
        matchResults.clear();
        adapter.notifyDataSetChanged();

        String name = LocalAuthStore.getName(this);
        if (name == null || name.isEmpty()) {
            name = SessionManager.getFirstName(this);
        }
        List<String> interests = Arrays.asList(InziraPrefs.getInterests(this).split(","));
        List<String> skills = new ArrayList<>();
        String skillsStr = InziraPrefs.getSkills(this);
        if (skillsStr != null && !skillsStr.isEmpty()) {
            skills = Arrays.asList(skillsStr.split(","));
        }

        YouthProfileRequest profile = new YouthProfileRequest(
                name,
                InziraPrefs.getDistrict(this),
                InziraPrefs.getAge(this),
                InziraPrefs.getEducation(this),
                skills,
                interests);

        RetrofitClient.getApiService().youthMatches(profile).enqueue(new Callback<MatchesResponse>() {
            @Override
            public void onResponse(Call<MatchesResponse> call, Response<MatchesResponse> response) {
                progressMatches.setVisibility(View.GONE);
                if (response.isSuccessful() && response.body() != null) {
                    MatchesResponse body = response.body();
                    if (body.matches != null) {
                        matchResults.addAll(body.matches);
                    }
                    adapter.notifyDataSetChanged();
                    matchesHeader.setVisibility(View.VISIBLE);
                    profileProgressCard.setVisibility(View.VISIBLE);
                    profileProgressBar.setProgress(body.profile_completeness);
                    tvProfileScoreLabel.setText(
                            LanguageHelper.profileCompletenessLabel(MatchesActivity.this,
                                    body.profile_completeness));
                    tvProfileScore.setText(body.profile_completeness + "%");

                    if (body.insights != null && !body.insights.isEmpty()) {
                        StringBuilder insightText = new StringBuilder();
                        for (String line : body.insights) {
                            insightText.append("• ").append(line).append("\n");
                        }
                        tvInsights.setText(insightText.toString().trim());
                        tvInsights.setVisibility(View.VISIBLE);
                    } else {
                        tvInsights.setVisibility(View.GONE);
                    }
                    if (matchResults.isEmpty()) {
                        tvNoMatches.setVisibility(View.VISIBLE);
                        recyclerMatches.setVisibility(View.GONE);
                        tvNoMatches.setText(LanguageHelper.noMatchesYet(MatchesActivity.this));
                    } else {
                        tvNoMatches.setVisibility(View.GONE);
                        recyclerMatches.setVisibility(View.VISIBLE);
                    }
                } else {
                    tvNoMatches.setVisibility(View.VISIBLE);
                    tvNoMatches.setText(LanguageHelper.backendUnavailableResults(MatchesActivity.this));
                }
            }

            @Override
            public void onFailure(Call<MatchesResponse> call, Throwable t) {
                progressMatches.setVisibility(View.GONE);
                tvNoMatches.setVisibility(View.VISIBLE);
                tvNoMatches.setText(LanguageHelper.backendOfflineMessage(MatchesActivity.this));
            }
        });
    }

    private void applyLanguageUi() {
        boolean rw = InziraPrefs.isKinyarwanda(this);
        ((TextView) findViewById(R.id.tvMatchesTitle)).setText(rw ? "Amahirwe yanjye" : "My matches");
        ((TextView) findViewById(R.id.tvMatchesSubtitle)).setText(rw
                ? "Amahirwe akwiriye ukurikije umwirondoro wawe"
                : "Personalized opportunities based on your profile");
        ((TextView) findViewById(R.id.tvProfileTitle)).setText(rw ? "Umwirondoro wawe" : "Your profile");
        ((TextView) findViewById(R.id.tvProfileHint)).setText(rw
                ? "Dusobanure ibyerekeye wowe kugira ngo tubone ibikwiriye"
                : "Tell us about yourself to find your best matches");
        ((TextView) findViewById(R.id.tvDistrictFieldLabel)).setText(LanguageHelper.districtLabel(this));
        ((TextView) findViewById(R.id.tvAgeFieldLabel)).setText(LanguageHelper.ageLabel(this));
        ((TextView) findViewById(R.id.tvEducationLabel)).setText(LanguageHelper.educationLabel(this));
        ((TextView) findViewById(R.id.tvInterestsLabel)).setText(LanguageHelper.interestsLabel(this));
        ((Button) findViewById(R.id.btnSaveProfile)).setText(rw ? "Shaka amahirwe yanjye" : "Find my matches");
        ((TextView) findViewById(R.id.tvResultsTitle)).setText(rw ? "Amahirwe yawe" : "Your matches");
        tvNoMatches.setText(rw
                ? "Uzuza umwirondoro wawe hanyuma ukande Shaka amahirwe yanjye"
                : "Complete your profile and tap Find my matches");
    }

    @Override
    protected void onResume() {
        super.onResume();
        applyLanguageUi();
    }
}
