package com.newaitiku.chemistry;

import gov.nih.ncats.molvec.Molvec;
import java.io.File;

public final class MolvecRunner {
    private MolvecRunner() {}

    public static void main(String[] args) throws Exception {
        if (args.length != 1) {
            System.err.println("usage: java -jar molvec-runner.jar <image-path>");
            System.exit(2);
        }
        File input = new File(args[0]);
        if (!input.isFile()) {
            System.err.println("image file not found: " + input.getAbsolutePath());
            System.exit(2);
        }
        String molfile = Molvec.ocr(input);
        String normalized = molfile == null ? "" : molfile.trim();
        System.out.println("{\"molfile\":\"" + escapeJson(normalized) + "\"}");
    }

    private static String escapeJson(String value) {
        StringBuilder builder = new StringBuilder();
        for (char current : value.toCharArray()) {
            switch (current) {
                case '\\':
                    builder.append("\\\\");
                    break;
                case '\"':
                    builder.append("\\\"");
                    break;
                case '\n':
                    builder.append("\\n");
                    break;
                case '\r':
                    builder.append("\\r");
                    break;
                case '\t':
                    builder.append("\\t");
                    break;
                default:
                    builder.append(current);
                    break;
            }
        }
        return builder.toString();
    }
}
