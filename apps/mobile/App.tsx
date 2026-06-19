import { StyleSheet, Text, View } from "react-native";
import { WebView } from "react-native-webview";
import { StatusBar } from "expo-status-bar";

/** After deploy, change to https://your-domain.com/studio */
const WEB_URL = "http://localhost:3000/studio";

export default function App() {
  const isLocal = WEB_URL.includes("localhost");

  return (
    <>
      <StatusBar style="light" />
      {isLocal ? (
        <View style={styles.container}>
          <Text style={styles.title}>RTAS Studio AI</Text>
          <Text style={styles.hint}>
            Deploy the web app, then set WEB_URL in App.tsx to your live URL for
            Play Store / App Store builds.
          </Text>
        </View>
      ) : (
        <WebView source={{ uri: WEB_URL }} style={styles.web} />
      )}
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0a0b10",
    justifyContent: "center",
    padding: 24,
  },
  title: { color: "#e8c547", fontSize: 22, fontWeight: "600", marginBottom: 12 },
  hint: { color: "#9aa3b8", lineHeight: 22 },
  web: { flex: 1 },
});
