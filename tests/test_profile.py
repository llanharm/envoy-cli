"""Tests for envoy.profile."""
import pytest
from pathlib import Path

from envoy.profile import Profile, ProfileError, ProfileStore


@pytest.fixture
def store(tmp_path):
    return ProfileStore(tmp_path / "profiles.json")


@pytest.fixture
def sample_profile(tmp_path):
    env = tmp_path / ".env"
    env.write_text("KEY=value\n")
    return Profile(name="dev", env_file=str(env), description="Dev env", tags=["dev"])


def test_add_profile_persists(store, sample_profile):
    store.add(sample_profile)
    assert store.get("dev").name == "dev"


def test_add_duplicate_raises(store, sample_profile):
    store.add(sample_profile)
    with pytest.raises(ProfileError, match="already exists"):
        store.add(sample_profile)


def test_remove_profile(store, sample_profile):
    store.add(sample_profile)
    store.remove("dev")
    with pytest.raises(ProfileError, match="not found"):
        store.get("dev")


def test_remove_missing_raises(store):
    with pytest.raises(ProfileError, match="not found"):
        store.remove("ghost")


def test_list_all_profiles(store, tmp_path):
    for name in ("dev", "staging", "prod"):
        env = tmp_path / f".env.{name}"
        env.write_text("K=v\n")
        store.add(Profile(name=name, env_file=str(env)))
    assert len(store.list_profiles()) == 3


def test_list_filtered_by_tag(store, tmp_path):
    for name, tags in (("dev", ["local"]), ("ci", ["remote"]), ("prod", ["remote"])):
        env = tmp_path / f".env.{name}"
        env.write_text("K=v\n")
        store.add(Profile(name=name, env_file=str(env), tags=tags))
    remote = store.list_profiles(tag="remote")
    assert {p.name for p in remote} == {"ci", "prod"}


def test_store_reloads_from_disk(tmp_path, sample_profile):
    path = tmp_path / "profiles.json"
    s1 = ProfileStore(path)
    s1.add(sample_profile)
    s2 = ProfileStore(path)  # fresh load
    assert s2.get("dev").description == "Dev env"


def test_profile_to_dict_roundtrip(sample_profile):
    d = sample_profile.to_dict()
    restored = Profile.from_dict(d)
    assert restored.name == sample_profile.name
    assert restored.tags == sample_profile.tags
