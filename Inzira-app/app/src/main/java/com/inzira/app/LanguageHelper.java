package com.inzira.app;

import android.content.Context;
import android.widget.EditText;
import android.widget.TextView;
import androidx.core.content.ContextCompat;

public final class LanguageHelper {

    private LanguageHelper() {
    }

    public static String welcomeSubtitle(Context context) {
        return isRw(context)
                ? "Republika y'u Rwanda · Urubuga rw'amahirwe y'urubyiruko"
                : "Republic of Rwanda · Youth opportunity platform";
    }

    public static String newToInziraPrompt(Context context) {
        return isRw(context) ? "Umusanzwe uri mushya kuri Inzira? " : "New to Inzira? ";
    }

    public static String createAnAccountLink(Context context) {
        return isRw(context) ? "Kora konti" : "Create an account";
    }

    public static String orContinueWith(Context context) {
        return isRw(context) ? "cyangwa komeza ukoresheje" : "or continue with";
    }

    public static String registerTitle(Context context) {
        return isRw(context) ? "Kora konti yawe" : "Create your account";
    }

    public static String registerSubtitle(Context context) {
        return isRw(context)
                ? "Jya mu banyarwanda benshi b'urubyiruko"
                : "Join thousands of Rwandan youth";
    }

    public static String fullNameLabel(Context context) {
        return isRw(context) ? "Amazina yuzuye" : "Full name";
    }

    public static String districtLabel(Context context) {
        return isRw(context) ? "Akarere" : "District";
    }

    public static String ageLabel(Context context) {
        return isRw(context) ? "Imyaka" : "Age";
    }

    public static String alreadyRegisteredPrompt(Context context) {
        return isRw(context) ? "Usanzwe wiyandikishije? " : "Already registered? ";
    }

    public static String termsText(Context context) {
        return isRw(context)
                ? "Nemeye amategeko ya serivisi. Ibikorwa byo gushakisha bishobora gukoreshwa mu bushakashatsi bw'igihugu ku rerekeza rw'urubyiruko."
                : "I agree to the terms of service. Anonymized search activity may inform national youth policy research.";
    }

    public static String createAccountButton(Context context) {
        return isRw(context) ? "Kora konti" : "Create account";
    }

    public static String getStarted(Context context) {
        return isRw(context) ? "Kora konti" : "Create account";
    }

    public static String signInButton(Context context) {
        return isRw(context) ? "Injira" : "Sign in";
    }

    public static String signOutButton(Context context) {
        return isRw(context) ? "Sohoka" : "Sign out";
    }

    public static String welcomeCardSubtitle(Context context) {
        return isRw(context)
                ? "Murakaza neza kuri Inzira"
                : "Welcome to Inzira";
    }

    public static String chooseLanguageLabel(Context context) {
        return isRw(context) ? "Hitamo ururimi" : "Choose your language";
    }

    public static String alreadyHaveAccountPrompt(Context context) {
        return isRw(context) ? "Usanzwe ufite konti? " : "Already have an account? ";
    }

    public static String newHerePrompt(Context context) {
        return isRw(context) ? "Ubu uri mushya? " : "New here? ";
    }

    public static String emailHint(Context context) {
        return isRw(context) ? "Imeyili" : "Email address";
    }

    public static String passwordHint(Context context) {
        return isRw(context) ? "Ijambo ry'ibanga" : "Password";
    }

    public static String forgotPasswordLabel(Context context) {
        return isRw(context) ? "Wibagiwe ijambo ry'ibanga?" : "Forgot password?";
    }

    public static String orLabel(Context context) {
        return isRw(context) ? "cyangwa" : "or";
    }

    public static String continueWithGoogle(Context context) {
        return isRw(context) ? "Komeza na Google" : "Continue with Google";
    }

    public static String forgotPasswordHint(Context context) {
        return isRw(context)
                ? "Koresha imeyili wiyandikishije, cyangwa kora konti nshya."
                : "Use the email you registered with, or create a new account.";
    }

    public static String googleSignInHint(Context context) {
        return isRw(context)
                ? "Kwinjira na Google bizaza vuba — koresha imeyili ubu."
                : "Google sign-in coming soon — use email for now.";
    }

    public static String signInLink(Context context) {
        return isRw(context) ? "Injira" : "Sign in";
    }

    public static String welcomeTagline(Context context) {
        return isRw(context)
                ? "Inzira bisobanura INZIRA mu Kinyarwanda"
                : "Inzira means PATH in Kinyarwanda";
    }

    public static String continueLabel(Context context) {
        return isRw(context) ? "Komeza" : "Continue";
    }

    public static String educationLabel(Context context) {
        return isRw(context) ? "Amashuri / inyigisho" : "Education / studies";
    }

    public static String interestsLabel(Context context) {
        return isRw(context) ? "Ibyo ukunda" : "Interest fields";
    }

    public static String selectDistrictToast(Context context) {
        return isRw(context) ? "Hitamo akarere" : "Please select your district";
    }

    public static String selectAgeToast(Context context) {
        return isRw(context) ? "Hitamo imyaka" : "Please select your age";
    }

    public static String selectEducationToast(Context context) {
        return isRw(context) ? "Hitamo amashuri" : "Please select your education";
    }

    public static String selectInterestsToast(Context context) {
        return isRw(context) ? "Hitamo byibuze ikintu kimwe ukunda" : "Please select at least one interest";
    }

    public static String noMatchesYet(Context context) {
        return isRw(context)
                ? "Nta mahirwe yabonetse — gerageza kongera nyuma"
                : "No matches found yet — try again later";
    }

    public static String purposeScholarships(Context context) {
        return isRw(context) ? "Amabwiriza" : "Scholarships";
    }

    public static String purposeJobs(Context context) {
        return isRw(context) ? "Akazi" : "Jobs";
    }

    public static String purposeEligibility(Context context) {
        return isRw(context) ? "Uburenganzira" : "Eligibility";
    }

    public static String assistantPurposePrompt(Context context) {
        return isRw(context)
                ? "Muraho! Hitamo intego imwe hepfo, hanyuma ubaze ikibazo cyawe."
                : "Muraho! Choose one purpose below, then ask your question.";
    }

    public static String assistantPurposeWelcome(Context context, String purpose) {
        if (AssistantActivity.PURPOSE_SCHOLARSHIPS.equals(purpose)) {
            return isRw(context)
                    ? "Nzagufasha kubona amabwiriza n'ubufasha mu Rwanda. Wandika icyo ushaka."
                    : "I'll help you find scholarships and funding in Rwanda. What are you looking for?";
        }
        if (AssistantActivity.PURPOSE_JOBS.equals(purpose)) {
            return isRw(context)
                    ? "Nzagufasha kubona akazi n'imyitozo mu Rwanda. Wandika icyo ushaka."
                    : "I'll help you find jobs and internships in Rwanda. What are you looking for?";
        }
        return isRw(context)
                ? "Nzagusobanurira niba wujuje ibisabwa n'uburenganzira bw'amahirwe. Sobanura amahirwe ushaka."
                : "I'll explain eligibility and requirements for opportunities. Describe what you're interested in.";
    }

    public static String assistantInputHint(Context context) {
        return isRw(context) ? "Andika ikibazo cyawe..." : "Type your question...";
    }

    public static String selectPurposeToast(Context context) {
        return isRw(context) ? "Hitamo intego imwe mbere" : "Please choose a purpose first";
    }

    public static String dashboardOpportunitiesLabel(Context context) {
        return isRw(context) ? "AMAHIRWE" : "OPPORTUNITIES";
    }

    public static String dashboardTapDistrict(Context context) {
        return isRw(context) ? "Kanda akarere ku ikarita" : "Tap a district on the map";
    }

    public static String dashboardMapHint(Context context) {
        return isRw(context)
                ? "Uturere twijimye = amahirwe menshi"
                : "Darker areas have more verified opportunities";
    }

    public static String dashboardSelectDistrict(Context context) {
        return isRw(context)
                ? "Hitamo akarere kugira ngo ubone amahirwe"
                : "Select a district to explore opportunities";
    }

    public static String dashboardNoSites(Context context) {
        return isRw(context)
                ? "Nta mahirwe yabonetse muri aka karere"
                : "No opportunities found for this district yet";
    }

    public static String dashboardSitesCount(Context context, int count) {
        return isRw(context) ? count + " amahirwe" : count + " opportunities";
    }

    public static String legendLow(Context context) {
        return isRw(context) ? "Bike" : "Low";
    }

    public static String legendHigh(Context context) {
        return isRw(context) ? "Cyane" : "High";
    }

    public static String matchFitLabel(Context context) {
        return isRw(context) ? "Guhuza" : "Match fit";
    }

    public static String whyYouFit(Context context) {
        return isRw(context) ? "Impamvu ujyana" : "Why you fit";
    }

    public static String matchTier(Context context, int score) {
        if (score >= 80) {
            return isRw(context) ? "Guhuza neza cyane" : "Strong match";
        }
        if (score >= 65) {
            return isRw(context) ? "Guhuza neza" : "Good match";
        }
        if (score >= 50) {
            return isRw(context) ? "Bishoboka" : "Possible match";
        }
        return isRw(context) ? "Buke buke" : "Low match";
    }

    public static String competitionLabel(Context context, String level) {
        if (level == null) {
            return "";
        }
        switch (level.toLowerCase()) {
            case "high":
                return isRw(context) ? "Irushanwa rikomeye" : "High competition";
            case "medium":
                return isRw(context) ? "Irushanwa riciriritse" : "Medium competition";
            case "low":
                return isRw(context) ? "Irushanwa rike" : "Low competition";
            default:
                return "";
        }
    }

    public static String profileCompletenessLabel(Context context, int percent) {
        return isRw(context)
                ? "Umwirondoro wuzuye " + percent + "%"
                : "Profile " + percent + "% complete";
    }

    public static String assistantError(Context context) {
        return isRw(context)
                ? "Ihangane, habaye ikosa. Ongera ugerageze."
                : "Sorry, something went wrong. Please try again.";
    }

    public static String assistantOffline(Context context) {
        return isRw(context)
                ? "Ntibyashoboye guhuza na seriveri. Reba niba backend ikora."
                : "Could not connect to server. Make sure the backend is running.";
    }

    public static String buildAssistantMessage(Context context, String purpose, String userMessage) {
        String prefix;
        if (AssistantActivity.PURPOSE_SCHOLARSHIPS.equals(purpose)) {
            prefix = isRw(context)
                    ? "[INTENGO: Amabwiriza mu Rwanda] "
                    : "[PURPOSE: Find scholarships in Rwanda] ";
        } else if (AssistantActivity.PURPOSE_JOBS.equals(purpose)) {
            prefix = isRw(context)
                    ? "[INTENGO: Akazi n'imyitozo mu Rwanda] "
                    : "[PURPOSE: Find jobs and internships in Rwanda] ";
        } else {
            prefix = isRw(context)
                    ? "[INTENGO: Sobanura uburenganzira] "
                    : "[PURPOSE: Explain eligibility requirements] ";
        }
        return prefix + userMessage;
    }

    public static String assistantWelcome(Context context) {
        return isRw(context)
                ? "Muraho! Ndi umuyobozi wa AI wa Inzira. Nshobora kugufasha kubona imbuga nkoranyambaga z'amahirwe mu Rwanda. Ushaka iki?"
                : "Muraho! I am the Inzira AI assistant. I can help you discover websites hosting opportunities in Rwanda. What are you looking for?";
    }

    public static String searchHint(Context context) {
        return isRw(context)
                ? "Shakisha amabwiriza, akazi, amahugurwa..."
                : "Search scholarships, jobs, programs...";
    }

    public static String murahoLabel(Context context) {
        return isRw(context) ? "Muraho," : "Hello,";
    }

    public static String murahoWelcomeGuest(Context context) {
        return isRw(context) ? "Muraho!" : "Welcome!";
    }

    public static String enterAppLabel(Context context) {
        return isRw(context) ? "Shakisha amahirwe" : "Find opportunities";
    }

    public static String lookingForTitle(Context context) {
        return isRw(context)
                ? "Ushaka iki uyu munsi?"
                : "What are you looking for today?";
    }

    public static String lookingForDescription(Context context) {
        return isRw(context)
                ? "Shakisha cyangwa kanda ku cyiciro kugira ngo ubone imbuga zose zitanga amahirwe mu Rwanda."
                : "Find every website in Rwanda that hosts the type of opportunities you are looking for.";
    }

    public static String howItWorksTitle(Context context) {
        return isRw(context) ? "Inzira ikora gute" : "How Inzira works";
    }

    public static String[] howItWorksSteps(Context context) {
        if (isRw(context)) {
            return new String[]{
                    "Andika ibyo ushaka gushakisha",
                    "Inzira isuzuma interineti mu gihe nyacyo",
                    "AI isuzuma ukuri n'icyiciro",
                    "Ujya ku rubuga usaba"
            };
        }
        return new String[]{
                "Type what you are looking for",
                "Inzira scans the web in real time",
                "AI verifies trust and category",
                "You visit the source and apply"
        };
    }

    public static String chipScholarships(Context context) {
        return isRw(context) ? "Amabwiriza" : "Scholarships";
    }

    public static String chipJobs(Context context) {
        return isRw(context) ? "Akazi" : "Jobs";
    }

    public static String chipInternships(Context context) {
        return isRw(context) ? "Internship" : "Internships";
    }

    public static String chipPrograms(Context context) {
        return isRw(context) ? "Programu" : "Programs";
    }

    public static String chipTraining(Context context) {
        return isRw(context) ? "Amahugurwa" : "Training";
    }

    public static String chipCompetitions(Context context) {
        return isRw(context) ? "Irushanwa" : "Competitions";
    }

    public static String chipCourses(Context context) {
        return isRw(context) ? "Amasomo yubusa" : "Free Courses";
    }

    public static String backendOfflineMessage(Context context) {
        return isRw(context)
                ? "Seriveri ntabwo ikora. Tangiza backend: python main.py"
                : "Backend not running. Start it with: python main.py";
    }

    public static String searchingWebsites(Context context) {
        return isRw(context) ? "Gushaka amahirwe..." : "Loading opportunities...";
    }

    public static String noVerifiedWebsitesYet(Context context) {
        return isRw(context)
                ? "Nta mahirwe yabonetse — seriveri igomba gukora refresh"
                : "No opportunities yet — run: python build_registry.py opportunities";
    }

    public static String verifiedWebsitesCount(Context context, int count, String query) {
        return isRw(context)
                ? count + " amahirwe — " + query
                : count + " verified opportunities — " + query;
    }

    public static String backendUnavailableResults(Context context) {
        return isRw(context)
                ? "Ntibyashoboye guhuza na seriveri"
                : "Could not reach Inzira server";
    }

    public static void applyLanguageChipStyle(Context context, TextView btnEnglish, TextView btnKinyarwanda) {
        if (isRw(context)) {
            btnKinyarwanda.setBackgroundResource(R.drawable.bg_lang_chip_selected);
            btnKinyarwanda.setTextColor(ContextCompat.getColor(context, R.color.white));
            btnKinyarwanda.setTypeface(btnKinyarwanda.getTypeface(), android.graphics.Typeface.BOLD);
            btnEnglish.setBackgroundResource(R.drawable.bg_lang_chip_outline);
            btnEnglish.setTextColor(ContextCompat.getColor(context, R.color.text_secondary));
            btnEnglish.setTypeface(btnEnglish.getTypeface(), android.graphics.Typeface.NORMAL);
        } else {
            btnEnglish.setBackgroundResource(R.drawable.bg_lang_chip_selected);
            btnEnglish.setTextColor(ContextCompat.getColor(context, R.color.white));
            btnEnglish.setTypeface(btnEnglish.getTypeface(), android.graphics.Typeface.BOLD);
            btnKinyarwanda.setBackgroundResource(R.drawable.bg_lang_chip_outline);
            btnKinyarwanda.setTextColor(ContextCompat.getColor(context, R.color.text_secondary));
            btnKinyarwanda.setTypeface(btnKinyarwanda.getTypeface(), android.graphics.Typeface.NORMAL);
        }
    }

    public static void applyWelcomeScreen(Context context,
                                          TextView tvHeaderSubtitle,
                                          TextView tvEmailLabel,
                                          TextView tvPasswordLabel,
                                          TextView btnSignIn,
                                          TextView etEmail,
                                          TextView btnGoogle,
                                          TextView tvForgotPassword,
                                          TextView tvOr,
                                          TextView tvNewHerePrompt,
                                          TextView tvCreateAccountLink) {
        tvHeaderSubtitle.setText(welcomeSubtitle(context));
        tvEmailLabel.setText(emailHint(context));
        tvPasswordLabel.setText(passwordHint(context));
        btnSignIn.setText(signInButton(context));
        btnGoogle.setText(continueWithGoogle(context));
        tvForgotPassword.setText(forgotPasswordLabel(context));
        tvOr.setText(orContinueWith(context));
        tvNewHerePrompt.setText(newToInziraPrompt(context));
        tvCreateAccountLink.setText(createAnAccountLink(context));
    }

    public static void applyRegisterScreen(Context context,
                                           TextView tvRegisterTitle,
                                           TextView tvRegisterSubtitle,
                                           TextView tvNameLabel,
                                           TextView tvDistrictLabel,
                                           TextView tvAgeLabel,
                                           TextView tvEmailLabel,
                                           TextView tvPasswordLabel,
                                           EditText etName,
                                           EditText etEmail,
                                           TextView tvTerms,
                                           TextView btnRegister,
                                           TextView tvAlreadyRegistered,
                                           TextView tvLogin) {
        tvRegisterTitle.setText(registerTitle(context));
        tvRegisterSubtitle.setText(registerSubtitle(context));
        tvNameLabel.setText(fullNameLabel(context));
        tvDistrictLabel.setText(districtLabel(context));
        tvAgeLabel.setText(ageLabel(context));
        tvEmailLabel.setText(emailHint(context));
        tvPasswordLabel.setText(passwordHint(context));
        etName.setHint(isRw(context) ? "Liliane Umwanankabandi" : "Liliane Umwanankabandi");
        etEmail.setHint("liliane@example.com");
        tvTerms.setText(termsText(context));
        btnRegister.setText(createAccountButton(context));
        tvAlreadyRegistered.setText(alreadyRegisteredPrompt(context));
        tvLogin.setText(signInLink(context));
    }

    public static void applySearchScreen(Context context,
                                         EditText etSearch,
                                         TextView tvVerifiedSubtitle,
                                         TextView tvHowItWorksTitle,
                                         TextView tvStep1,
                                         TextView tvStep2,
                                         TextView tvStep3,
                                         TextView tvStep4,
                                         TextView chipAll,
                                         TextView chipScholarships,
                                         TextView chipJobs,
                                         TextView chipInternships,
                                         TextView chipPrograms,
                                         TextView chipTraining,
                                         TextView chipCompetitions,
                                         TextView chipCourses) {
        etSearch.setHint(searchHint(context));
        tvVerifiedSubtitle.setText(isRw(context)
                ? "Byemejwe na AI · Urubuga rw'urubyiruko mu Rwanda"
                : "AI-verified · Republic of Rwanda youth platform");
        tvHowItWorksTitle.setText(howItWorksTitle(context));
        String[] steps = howItWorksSteps(context);
        tvStep1.setText(steps[0]);
        tvStep2.setText(steps[1]);
        tvStep3.setText(steps[2]);
        tvStep4.setText(steps[3]);
        chipAll.setText(isRw(context) ? "Byose" : "All");
        chipScholarships.setText(chipScholarships(context));
        chipJobs.setText(chipJobs(context));
        chipInternships.setText(chipInternships(context));
        chipPrograms.setText(chipPrograms(context));
        chipTraining.setText(chipTraining(context));
        chipCompetitions.setText(chipCompetitions(context));
        chipCourses.setText(chipCourses(context));
    }

    private static boolean isRw(Context context) {
        return InziraPrefs.isKinyarwanda(context);
    }
}
