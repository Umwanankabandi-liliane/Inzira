package com.inzira.app;

import android.content.Context;
import android.widget.ArrayAdapter;
import android.widget.Spinner;

public final class DistrictHelper {

    private DistrictHelper() {
    }

    public static void setupSpinner(Context context, Spinner spinner) {
        ArrayAdapter<CharSequence> adapter = ArrayAdapter.createFromResource(
                context, R.array.rwanda_districts, android.R.layout.simple_spinner_item);
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        spinner.setAdapter(adapter);
    }

    public static String selectedDistrict(Spinner spinner) {
        if (spinner.getSelectedItem() == null) {
            return "";
        }
        String value = spinner.getSelectedItem().toString().trim();
        if (value.isEmpty() || value.startsWith("Select")) {
            return "";
        }
        return value;
    }

    public static void selectDistrict(Spinner spinner, String district) {
        if (district == null || district.isEmpty()) {
            return;
        }
        ArrayAdapter adapter = (ArrayAdapter) spinner.getAdapter();
        if (adapter == null) {
            return;
        }
        for (int i = 0; i < adapter.getCount(); i++) {
            if (district.equalsIgnoreCase(adapter.getItem(i).toString())) {
                spinner.setSelection(i);
                return;
            }
        }
    }

    /** Display name for UI labels (bottom panel only — map stays label-free). */
    public static String displayName(Context context, String district) {
        if (district == null || district.isEmpty()) {
            return "";
        }
        if (!InziraPrefs.isKinyarwanda(context)) {
            return district;
        }
        return "Akarere ka " + district;
    }
}
