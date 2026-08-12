import { StatusBar } from 'expo-status-bar';
import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Linking,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

// Android emulator reaches the host via 10.0.2.2; iOS simulator / web use localhost.
const API_BASE = Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://localhost:8000';

type DigestItem = {
  id: string;
  source: string;
  title?: string;
  short?: string;
  long?: string;
  url?: string;
  author?: string;
  score?: number;
};

type DigestTopic = {
  topic: string;
  summary?: string;
  items: DigestItem[];
};

type Digest = {
  date: string;
  generated_at?: string;
  topics: DigestTopic[];
};

export default function App() {
  const [topics, setTopics] = useState<string[]>([]);
  const [input, setInput] = useState('');
  const [digest, setDigest] = useState<Digest | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadTopics = useCallback(async () => {
    try {
      const r = await fetch(`${API_BASE}/topics`);
      const data = await r.json();
      setTopics((data as { raw_prompt: string }[]).map((t) => t.raw_prompt));
    } catch {
      /* backend not reachable yet */
    }
  }, []);

  const loadDigest = useCallback(async () => {
    try {
      const r = await fetch(`${API_BASE}/digest/today`);
      if (r.ok) setDigest(await r.json());
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    loadTopics();
    loadDigest();
  }, [loadTopics, loadDigest]);

  const addTopic = async () => {
    const prompt = input.trim();
    if (!prompt) return;
    setLoading(true);
    setError(null);
    try {
      const merged = Array.from(new Set([...topics.filter((t) => t !== prompt), prompt]));
      const r = await fetch(`${API_BASE}/topics`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topics: merged.map((t) => ({ raw_prompt: t })) }),
      });
      if (!r.ok) throw new Error(`topics ${r.status}`);
      const data = (await r.json()) as { raw_prompt: string }[];
      setTopics(data.map((t) => t.raw_prompt));
      setInput('');
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const refresh = async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(`${API_BASE}/refresh`, { method: 'POST' });
      if (!r.ok) throw new Error(`refresh ${r.status}`);
      setDigest(await r.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.screen}>
      <StatusBar style="light" />
      <View style={styles.header}>
        <Text style={styles.title}>Daily Digest</Text>
        <Text style={styles.subtitle}>{API_BASE}</Text>
      </View>

      <View style={styles.controls}>
        <TextInput
          style={styles.input}
          placeholder="Add a topic (e.g. 'oracle cloud')"
          placeholderTextColor="#8892a0"
          value={input}
          onChangeText={setInput}
          onSubmitEditing={addTopic}
          returnKeyType="done"
        />
        <Pressable style={styles.button} onPress={addTopic} disabled={loading}>
          <Text style={styles.buttonText}>Add</Text>
        </Pressable>
        <Pressable style={[styles.button, styles.refresh]} onPress={refresh} disabled={loading}>
          {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Refresh digest</Text>}
        </Pressable>
      </View>

      {topics.length > 0 && (
        <View style={styles.topicRow}>
          {topics.map((t) => (
            <View key={t} style={styles.chip}>
              <Text style={styles.chipText}>{t}</Text>
            </View>
          ))}
        </View>
      )}

      {error && <Text style={styles.error}>{error}</Text>}

      <ScrollView contentContainerStyle={styles.body}>
        {digest && digest.topics.length === 0 && (
          <Text style={styles.empty}>No topics yet — add one above, then refresh.</Text>
        )}
        {digest?.topics.map((topic) => (
          <View key={topic.topic} style={styles.card}>
            <Text style={styles.topicName}>{topic.topic}</Text>
            <Text style={styles.summary}>{topic.summary}</Text>
            {topic.items.map((item) => (
              <Pressable
                key={item.id}
                style={styles.item}
                onPress={() => item.url && Linking.openURL(item.url)}
              >
                <Text style={styles.itemTitle}>{item.title}</Text>
                <Text style={styles.meta}>
                  {item.source} · {item.author ?? 'unknown'} · {item.score ?? 0} pts
                </Text>
                {item.short && item.short !== item.title && (
                  <Text style={styles.itemShort}>{item.short}</Text>
                )}
              </Pressable>
            ))}
          </View>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#0f1115' },
  header: { paddingTop: 56, paddingHorizontal: 20, paddingBottom: 12 },
  title: { color: '#e6edf3', fontSize: 26, fontWeight: '700' },
  subtitle: { color: '#6e7681', fontSize: 12, marginTop: 2 },
  controls: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 20, gap: 8 },
  input: {
    flex: 1,
    backgroundColor: '#1c2128',
    color: '#e6edf3',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 15,
  },
  button: { backgroundColor: '#316dca', borderRadius: 8, paddingHorizontal: 14, paddingVertical: 10 },
  refresh: { backgroundColor: '#2ea043' },
  buttonText: { color: '#fff', fontWeight: '600' },
  topicRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, paddingHorizontal: 20, paddingTop: 12 },
  chip: { backgroundColor: '#1c2128', borderRadius: 14, paddingHorizontal: 10, paddingVertical: 5 },
  chipText: { color: '#7ee787', fontSize: 12 },
  error: { color: '#ff7b72', paddingHorizontal: 20, paddingTop: 8 },
  body: { padding: 20, gap: 14, paddingBottom: 40 },
  empty: { color: '#6e7681', textAlign: 'center', marginTop: 40 },
  card: { backgroundColor: '#161b22', borderRadius: 10, padding: 16, gap: 10 },
  topicName: { color: '#e6edf3', fontSize: 18, fontWeight: '700' },
  summary: { color: '#9da7b3', fontSize: 14, lineHeight: 20 },
  item: { borderTopWidth: 1, borderTopColor: '#21262d', paddingTop: 10 },
  itemTitle: { color: '#e6edf3', fontSize: 15, fontWeight: '600' },
  meta: { color: '#6e7681', fontSize: 12, marginTop: 3 },
  itemShort: { color: '#9da7b3', fontSize: 13, marginTop: 4 },
});
