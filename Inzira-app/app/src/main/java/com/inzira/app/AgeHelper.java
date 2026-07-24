package com.inzira.app;

import android.content.Context;
import android.widget.ArrayAdapter;
import android.widget.Spinner;

public final class AgeHelper {

    private AgeHelper() {
    }

    public static void setupSpinner(Context context, Spinner spinner) {
        ArrayAdapter<CharSequence> adapter = ArrayAdapter.createFromResource(
                context, R.array.age_ranges, android.R.layout.simple_spinner_item);
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        spinner.setAdapter(adapter);
    }

    public static String selectedAge(Spinner spinner) {
        Object item = spinner.getSelectedItem();
        if (item == null) {
            return "";
        }
        String age = item.toString().trim();
        if (age.isEmpty() || age.toLowerCase().startsWith("select")) {
            return "";
        }
        return age;
    }

    public static void selectAge(Spinner spinner, String age) {
        if (age == null || age.isEmpty()) {
            return;
        }
        ArrayAdapter adapter = (ArrayAdapter) spinner.getAdapter();
        if (adapter == null) {
            return;
        }
        for (int i = 0; i < adapter.getCount(); i++) {
            if (age.equalsIgnoreCase(adapter.getItem(i).toString())) {
                spinner.setSelection(i);
                return;
            }
        }
    }
}
