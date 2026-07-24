package com.inzira.app;

import android.content.Context;
import android.widget.ArrayAdapter;
import android.widget.Spinner;

public final class EducationHelper {

    private EducationHelper() {
    }

    public static void setupSpinner(Context context, Spinner spinner) {
        ArrayAdapter<CharSequence> adapter = ArrayAdapter.createFromResource(
                context, R.array.education_levels, android.R.layout.simple_spinner_item);
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        spinner.setAdapter(adapter);
    }

    public static String selectedEducation(Spinner spinner) {
        String value = spinner.getSelectedItem() != null
                ? spinner.getSelectedItem().toString().trim() : "";
        if (value.startsWith("Select")) {
            return "";
        }
        return value;
    }

    public static void selectEducation(Spinner spinner, String education) {
        ArrayAdapter adapter = (ArrayAdapter) spinner.getAdapter();
        if (adapter == null) {
            return;
        }
        for (int i = 0; i < adapter.getCount(); i++) {
            Object item = adapter.getItem(i);
            if (item != null && item.toString().equals(education)) {
                spinner.setSelection(i);
                return;
            }
        }
    }
}
