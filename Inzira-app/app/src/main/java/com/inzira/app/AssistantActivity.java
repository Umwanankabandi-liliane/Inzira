package com.inzira.app;

import android.os.Bundle;
import android.view.View;
import android.view.inputmethod.EditorInfo;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import com.google.android.material.bottomnavigation.BottomNavigationView;
import java.util.ArrayList;
import java.util.List;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class AssistantActivity extends AppCompatActivity {

    public static final String PURPOSE_SCHOLARSHIPS = "scholarships";
    public static final String PURPOSE_JOBS = "jobs";
    public static final String PURPOSE_ELIGIBILITY = "eligibility";

    private final List<ChatMessage> messages = new ArrayList<>();
    private ChatAdapter adapter;
    private RecyclerView recyclerView;
    private EditText etMessage;
    private ImageButton btnSend;
    private TextView chipScholarships;
    private TextView chipJobs;
    private TextView chipEligibility;
    private String selectedPurpose = null;
    private boolean waitingForResponse = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        if (!SessionManager.isLoggedIn(this)) {
            NavHelper.openLogin(this, false, false);
            finish();
            return;
        }

        setContentView(R.layout.activity_assistant);

        recyclerView = findViewById(R.id.recyclerView);
        etMessage = findViewById(R.id.etMessage);
        btnSend = findViewById(R.id.btnSend);
        chipScholarships = findViewById(R.id.chipScholarships);
        chipJobs = findViewById(R.id.chipJobs);
        chipEligibility = findViewById(R.id.chipEligibility);
        BottomNavigationView bottomNav = findViewById(R.id.bottomNav);

        LinearLayoutManager layoutManager = new LinearLayoutManager(this);
        layoutManager.setStackFromEnd(true);
        recyclerView.setLayoutManager(layoutManager);
        adapter = new ChatAdapter(messages);
        recyclerView.setAdapter(adapter);

        applyLanguageUi();
        addBotMessage(LanguageHelper.assistantPurposePrompt(this));

        findViewById(R.id.btnClear).setOnClickListener(v -> {
            messages.clear();
            adapter.notifyDataSetChanged();
            selectedPurpose = null;
            updatePurposeChips();
            addBotMessage(LanguageHelper.assistantPurposePrompt(this));
        });

        chipScholarships.setOnClickListener(v -> selectPurpose(PURPOSE_SCHOLARSHIPS));
        chipJobs.setOnClickListener(v -> selectPurpose(PURPOSE_JOBS));
        chipEligibility.setOnClickListener(v -> selectPurpose(PURPOSE_ELIGIBILITY));

        btnSend.setOnClickListener(v -> sendCurrentMessage());
        etMessage.setOnEditorActionListener((v, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_SEND) {
                sendCurrentMessage();
                return true;
            }
            return false;
        });

        NavHelper.wireBottomNav(this, bottomNav, R.id.navAssistant);
    }

    private void applyLanguageUi() {
        boolean rw = InziraPrefs.isKinyarwanda(this);
        ((TextView) findViewById(R.id.tvAssistantTitle)).setText(rw ? "Umuyobozi wa AI" : "AI assistant");
        ((TextView) findViewById(R.id.tvAssistantSubtitle)).setText(rw
                ? "Hitamo intego imwe, hanyuma ubaze"
                : "Choose one purpose, then ask your question");
        chipScholarships.setText(LanguageHelper.purposeScholarships(this));
        chipJobs.setText(LanguageHelper.purposeJobs(this));
        chipEligibility.setText(LanguageHelper.purposeEligibility(this));
        etMessage.setHint(LanguageHelper.assistantInputHint(this));
    }

    private void selectPurpose(String purpose) {
        selectedPurpose = purpose;
        updatePurposeChips();
        String welcome = LanguageHelper.assistantPurposeWelcome(this, purpose);
        messages.clear();
        adapter.notifyDataSetChanged();
        addBotMessage(welcome);
    }

    private void updatePurposeChips() {
        chipScholarships.setBackgroundResource(
                PURPOSE_SCHOLARSHIPS.equals(selectedPurpose)
                        ? R.drawable.bg_filter_chip_active : R.drawable.bg_filter_chip);
        chipJobs.setBackgroundResource(
                PURPOSE_JOBS.equals(selectedPurpose)
                        ? R.drawable.bg_filter_chip_active : R.drawable.bg_filter_chip);
        chipEligibility.setBackgroundResource(
                PURPOSE_ELIGIBILITY.equals(selectedPurpose)
                        ? R.drawable.bg_filter_chip_active : R.drawable.bg_filter_chip);
    }

    private void sendCurrentMessage() {
        if (waitingForResponse) {
            return;
        }
        if (selectedPurpose == null) {
            Toast.makeText(this, LanguageHelper.selectPurposeToast(this), Toast.LENGTH_SHORT).show();
            return;
        }

        String message = etMessage.getText().toString().trim();
        if (message.isEmpty()) {
            return;
        }

        etMessage.setText("");
        addUserMessage(message);
        requestAssistantReply(message);
    }

    private void requestAssistantReply(String message) {
        waitingForResponse = true;
        btnSend.setEnabled(false);
        addBotMessage("...");
        final int typingIndex = messages.size() - 1;

        String contextualMessage = LanguageHelper.buildAssistantMessage(this, selectedPurpose, message);
        String language = InziraPrefs.getLanguage(this);

        RetrofitClient.getApiService()
                .assistant(new AssistantRequest(contextualMessage, language))
                .enqueue(new Callback<AssistantResponse>() {
                    @Override
                    public void onResponse(Call<AssistantResponse> call, Response<AssistantResponse> response) {
                        waitingForResponse = false;
                        btnSend.setEnabled(true);
                        removeMessageAt(typingIndex);

                        if (response.isSuccessful() && response.body() != null
                                && response.body().response != null && !response.body().response.isEmpty()) {
                            addBotMessage(response.body().response);
                        } else {
                            addBotMessage(LanguageHelper.assistantError(AssistantActivity.this));
                        }
                    }

                    @Override
                    public void onFailure(Call<AssistantResponse> call, Throwable t) {
                        waitingForResponse = false;
                        btnSend.setEnabled(true);
                        removeMessageAt(typingIndex);
                        addBotMessage(LanguageHelper.assistantOffline(AssistantActivity.this));
                    }
                });
    }

    private void addUserMessage(String text) {
        messages.add(new ChatMessage(text, true));
        adapter.notifyItemInserted(messages.size() - 1);
        scrollToBottom();
    }

    private void addBotMessage(String text) {
        messages.add(new ChatMessage(text, false));
        adapter.notifyItemInserted(messages.size() - 1);
        scrollToBottom();
    }

    private void removeMessageAt(int index) {
        if (index >= 0 && index < messages.size()) {
            messages.remove(index);
            adapter.notifyItemRemoved(index);
        }
    }

    private void scrollToBottom() {
        if (!messages.isEmpty()) {
            recyclerView.scrollToPosition(messages.size() - 1);
        }
    }
}
